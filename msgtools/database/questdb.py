#!/usr/bin/python3
import datetime
import os
import time
import traceback
import requests

from msgtools.lib.messaging import Messaging
import msgtools.console.client

# for writes (doesn't do queries!!)
from questdb import ingress
# for queries
import psycopg

# this allows sending Messages as data to an QuestDB database
class QuestDBConnection:
    MAX_POINTS = 128
    PRINT_TIME_INTERVAL = 10.0
    def __init__(self, msgClient, dbname='messages', hostname='localhost', port=9009, username='root', password='root'):
        self.hostname = hostname
        self.port = port
        self.database=dbname
        # Need a questdb Sender for writing
        conf = "http::addr=%s:%s;username=%s;password=%s;" % (hostname, port, username, password)
        self.db_write = ingress.Sender.from_conf(conf)
        # Need a postgres interface for reading
        conn_str = 'user=%s password=%s host=%s port=%s dbname=qdb' % (username, password, hostname, port)
        self.db_read = psycopg.connect(conn_str, autocommit=True)
        self.msgClient = msgClient
        self.cookie = 0
        
        self.stats = DBStats()
        
        # History Data message has to have either just Data with interleaved value and time,
        # or be an array of structs which also interleaves value and time in memory, but
        # gives two functions to access them that each look like an array.
        self.dataInfo = Messaging.findFieldInfo(Messaging.Messages.Network.History.Data.fields, "Data")
        self.dataValueInfo = Messaging.findFieldInfo(Messaging.Messages.Network.History.Data.fields, "Data_Value")
        self.dataTimestampInfo = Messaging.findFieldInfo(Messaging.Messages.Network.History.Data.fields, "Data_Timestamp")
        if self.dataInfo != None:
            # multiply by 2 because the result includes a value and a timestamp
            self.dataResultSize = self.dataInfo.size *2
            self.dataResultOffset = self.dataInfo.offset
        else:
            # Size of a result includes size of the value and the timestamp.
            self.dataResultSize = self.dataValueInfo.size + self.dataTimestampInfo.size
            # This needs to be whichever element is first!
            self.dataResultOffset = min(self.dataValueInfo.offset,self.dataTimestampInfo.offset)
    
    @staticmethod
    def FormattedTime(floatTime):
        return str(int(floatTime * 1e9))

    def handle_message(self, msg):
        if msg.MsgName().startswith("Network"):
            if msg.MsgName() == "Network.History.GetData":
                self.handle_query(msg)
        else:
            self.store_message(msg)
    
    def handle_timeout(self):
        stats_str = self.stats.report_stats(time.time(), self.PRINT_TIME_INTERVAL)
        if stats_str:
            print(stats_str)
    
    def store_message(self, msg):
        try:
            timeVal = msg.hdr.GetTime()
            if timeVal == 0.0:
                timeVal = time.time()
            else:
                timeInfo = Messaging.findFieldInfo(msg.hdr.fields, "Time")
                maxTime = timeInfo.maxVal
                # if it's not big enough to be an absolute timestamp, give up on using it and just use current time
                if maxTime != "DBL_MAX" and (maxTime == 'FLT_MAX' or float(maxTime) <= 2**32):
                    raise AttributeError
                if timeInfo.units == "ms":
                    timeVal = timeVal * 1.0e-3
                elif timeInfo.units == "us":
                    timeVal = timeVal * 1.0e-6
                elif timeInfo.units == "ns":
                    timeVal = timeVal * 1.0e-9
            timeVal = datetime.datetime.fromtimestamp(timeVal, datetime.timezone.utc)
        except AttributeError:
            timeVal = datetime.datetime.now()

        class QuestDBData:
            def __init__(self, table_name, at):
                self.table_name = table_name
                self.at = at
                self.symbols = {}
                self.columns = {}

            def add_msg(msg):
                # Add header fields
                for fieldInfo in msg.hdr.fields:
                    if len(fieldInfo.bitfieldInfo) == 0:
                        if fieldInfo.idbits == 0 and fieldInfo.name != "Time" and fieldInfo.name != "DataLength":
                            self._add_field(fieldInfo, Messaging.get(msg.hdr, fieldInfo))
                    else:
                        for bitInfo in fieldInfo.bitfieldInfo:
                            if bitInfo.idbits == 0 and bitInfo.name != "Time" and bitInfo.name != "DataLength":
                                self._add_field(bitInfo, Messaging.get(msg.hdr, bitInfo))
                
                # Add body fields
                msgClass = type(msg)
                for fieldInfo in msgClass.fields:
                    if fieldInfo.count == 1:
                        if len(fieldInfo.bitfieldInfo) == 0:
                            self._add_field(fieldInfo.name, Messaging.get(msg, fieldInfo))
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                self._add_field(bitInfo.name, Messaging.get(msg, bitInfo))
                    else:
                        # flatten arrays
                        is_enum = len(field_info.enum) > 0
                        for i in range(0,fieldInfo.count):
                            if is_enum:
                                self.symbols[fieldInfo.name+"_"+str(i)] = Messaging.get(msg, fieldInfo, i)
                            else:
                                self.columns[fieldInfo.name+"_"+str(i)] = Messaging.get(msg, fieldInfo, i)

                # Can't store with no fields!  Add a boolean to indicate emptiness
                if len(self.columns) == 0 and len(self.symbols) == 0:
                    self.columns['[EMPTY]'] = True

            def _add_field(field_info, value):
                name = field_info.name
                is_enum = len(field_info.enum) > 0
                if is_enum:
                    self.symbols[name] = value
                else:
                    self.columns[name] = value

        questdb_data = QuestDBData(table_name=msg.MsgName(),at=str(timeVal))        
        questdb_data.add_msg(msg)

        # record how many messages and bytes came in
        self.stats.messages_in += 1
        self.stats.bytes_in += msg.hdr.SIZE + msg.hdr.GetDataLength()
        try:
            self.db_write.row(
                table_name=questdb_data.table_name,
                symbols=questdb_data.symbols,
                columns=questdb_data.columns,
                at=questdb_data.at)
            # QuestDB supports auto flushing, which defaults to on, and is configured when the Sender
            # is created: https://py-questdb-client.readthedocs.io/en/latest/conf.html#sender-conf
            # You can specify a number of rows, numbers of bytes, and timeout for auto flushing.
            #self.db_write.flush()
            self.stats.messages_out += 1
            # we don't know exactly what gets written across the network to QuestDB, but
            # the length of the string of the JSON should be pretty close.
            self.stats.bytes_out += len(str(questdb_data))
        except requests.exceptions.ConnectionError:
            self.stats.connection_errors += 1
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            #print(dbJson)
            #print(msg)
            sys.exit()
    
    def handle_query(self, msg):
        msgquery = msg.GetQuery()
        msgAndFieldName = msgquery.split(",")[0]
        msgname = msgAndFieldName.split(".")[0]
        fieldname = msgAndFieldName.split(".")[1]
        tagQuery = msgquery.split(",")[1]
        if tagQuery != "":
            tagQuery += " AND "
        
        start = msg.GetStartTime()
        end = msg.GetEndTime()
        averagingPeriod = msg.GetAveragingPeriod()

        if averagingPeriod != 0:
            dbquery = 'SELECT "' + fieldname + '" FROM "' + msgname + '"'
        else:
            dbquery = 'SELECT MEAN("' + fieldname + '") FROM "' + msgname + '"'
        dbquery += " WHERE " + tagQuery + "time > " + FormattedTime(start)
        if end != 0:
            dbquery += " AND time < " + FormattedTime(end)
        else:
            end = datetime.datetime.now()
        if averagingPeriod != 0:
            # limit averaging period such that we don't get too many data points
            if avg / (end - start) > MAX_POINTS:
                avg = MAX_POINTS * (end - start)
            dbquery += " GROUP BY *,time("+FormattedTime(avg)+")"

        dbquery += " LIMIT " + str(MAX_POINTS)

        # send query to database, get results
        with self.db_read.cursor() as cursor:
            cursor.execute(dbquery)
            db_results = cursor.fetchall()

            # output results
            resultMsg = Messaging.Messages.Network.History.Result()
            resultMsg.SetCookie(self.cookie)
            resultCount = len(db_results)
            resultMsg.SetResultCount(resultCount)
            resultMsg.SetQuery(msgquery)
            self.msgClient.send_message(resultMsg)
            if self.dataInfo != None:
                maxDataPerMsg = self.dataInfo.count
            else:
                arrayOffset = self.dataTimestampInfo.offset
                arrayElemSize = self.dataValueInfo.size + dataTimestampInfo.size
                maxDataPerMsg = dataValueInfo.count
            resultMsgNumber = 0
            resultsLeftToSend = len(db_results)
            for result in db_results:
                print(results)
                dataMsg = Messaging.Messages.Network.History.Data()
                dataMsg.SetCookie(self.cookie)
                dataMsg.SetResultNumber(resultMsgNumber)
                dataRange = min(maxDataPerMsg, resultsLeftToSend)
                if self.dataInfo != None:
                    for index in range(0, dataRange,2):
                        dataMsg.SetData(time(result), index)
                        dataMsg.SetData(value(result), index+1)
                else:
                    for index in range(0, dataRange):
                        dataMsg.SetData_Timestamp(time(result), index)
                        dataMsg.SetData_Value(value(result), index)
                resultsLeftToSend -= dataRange
                resultMsgNumber += 1
                # truncate message buffer to actual amount of data
                msg_buffer_len = self.dataResultOffset + self.dataResultSize * dataRange
                self.msgClient.send_message(dataMsg)

        # Increment cookie so the next query's results are easy to tell apart from our query results
        # This is especially useful if two clients query at almost the same time (but only if they
        # have unique cookies!).
        self.cookie += 1

class DBStats:
    SUMMARY_FORMAT_STR = "{: >8}/{} msgs {: >8} bytes in {: >8} bytes out {: >8} cxn errors {: >8}/{} Msg/s {: >8} B/s in {: >8} B/s out {: >8} cxn errors/s"
    def __init__(self):
        self.messages_in = 0
        self.messages_out = 0
        self.bytes_in = 0
        self.bytes_out = 0
        self.connection_errors = 0
        self.last_time = 0
        self.last_messages_in = 0
        self.last_messages_out = 0
        self.last_bytes_in = 0
        self.last_bytes_out = 0
        self.last_connection_errors = 0
    
    def report_stats(self, now, time_interval):
        if now == None or now > self.last_time + time_interval:
            mips = (self.messages_in - self.last_messages_in)/time_interval
            mops = (self.messages_out - self.last_messages_out)/time_interval
            bips = (self.bytes_in - self.last_bytes_in)/time_interval
            bops = (self.bytes_out - self.last_bytes_out)/time_interval
            ceps = (self.connection_errors - self.last_connection_errors)/time_interval
            self.last_messages_in = self.messages_in
            self.last_messages_out = self.messages_out
            self.last_bytes_in = self.bytes_in
            self.last_bytes_out = self.bytes_out
            self.last_connection_errors = self.connection_errors
            self.last_time = now
            return self.SUMMARY_FORMAT_STR.format(
                self.messages_out, self.messages_in,
                self.bytes_in, self.bytes_out,
                self.connection_errors,
                mops, mips,
                bips, bops,
                ceps)
        return None

# this is client that reads from network, and writes to QuestDB
class QuestDBMsgClient:
    def __init__(self):
        Messaging.LoadAllMessages()

        self.connection = msgtools.console.client.Client("QuestDB")
        
        self.db = QuestDBConnection(self)
    
    def run(self):
        while True:
            # this blocks until message received, or timeout occurs
            timeout = 10.0 # value in seconds
            msg = self.connection.recv(timeout=timeout)
            if msg:
                self.db.handle_message(msg)
            self.db.handle_timeout()

# this is a CLI app that reads from network and writes to QuestDB
def main(args=None):
    dbClient = QuestDBMsgClient()
    try:
        dbClient.run()
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
        dbClient.connection.stop()

if __name__ == "__main__":
    main()
