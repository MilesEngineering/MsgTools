#!/usr/bin/python3
import datetime
import os
import time
import traceback
import requests

from msgtools.lib.messaging import Messaging
import msgtools.console.client

from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

# this allows sending Messages as data to an InfluxDB database
class InfluxDBConnection:
    MAX_POINTS = 128
    PRINT_TIME_INTERVAL = 10.0
    def __init__(self, msgClient, dbname='messages', hostname='localhost', port=8086, username='root', password='root'):
        self.hostname = hostname
        self.port = port
        self.db = InfluxDBClient(host=hostname, port=port, username=username, password=password, database=dbname)
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

        dbJson = {
                "time": str(timeVal),
                "measurement": msg.MsgName(),
                'fields':  {},
                'tags': {}
            }
        for fieldInfo in msg.hdr.fields:
            if len(fieldInfo.bitfieldInfo) == 0:
                if fieldInfo.idbits == 0 and fieldInfo.name != "Time" and fieldInfo.name != "DataLength":
                    dbJson['tags'][fieldInfo.name] = Messaging.get(msg.hdr, fieldInfo)
            else:
                for bitInfo in fieldInfo.bitfieldInfo:
                    if bitInfo.idbits == 0 and bitInfo.name != "Time" and bitInfo.name != "DataLength":
                        dbJson['tags'][bitInfo.name] = Messaging.get(msg.hdr, bitInfo)
        
        msgClass = type(msg)
        for fieldInfo in msgClass.fields:
            if fieldInfo.count == 1:
                if len(fieldInfo.bitfieldInfo) == 0:
                    dbJson['fields'][fieldInfo.name] = Messaging.get(msg, fieldInfo)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        dbJson['fields'][bitInfo.name] = Messaging.get(msg, bitInfo)
            else:
                # flatten arrays
                for i in range(0,fieldInfo.count):
                    dbJson['fields'][fieldInfo.name+"_"+str(i)] = Messaging.get(msg, fieldInfo, i)

        # Can't store with no fields!  Add a boolean to indicate emptiness
        if len(dbJson['fields']) == 0:
            dbJson['fields']['[EMPTY]'] = True

        #print("Create a retention policy")
        #retention_policy = 'awesome_policy'
        #client.create_retention_policy(retention_policy, '3d', 3, default=True)
        
        # record how many messages and bytes came in
        self.stats.messages_in += 1
        self.stats.bytes_in += msg.hdr.SIZE + msg.hdr.GetDataLength()
        try:
            self.db.write_points([dbJson]) #, retention_policy=retention_policy)
            self.stats.messages_out += 1
            # we don't know exactly what gets written across the network to InfluxDB, but
            # the length of the string of the JSON should be pretty close.
            self.stats.bytes_out += len(str(dbJson))
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
        db_results = self.db.query(dbquery)

        # output results
        resultMsg = Messaging.Messages.Network.History.Result()
        resultMsg.SetCookie(self.cookie)
        resultCount = f(db_results)
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

        # Increment cookie so the next query's results are easy to tell apart from out query results
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

# this is client that reads from network, and writes to InfluxDB
class InfluxDBMsgClient:
    def __init__(self):
        Messaging.LoadAllMessages()

        self.connection = msgtools.console.client.Client("InfluxDB")
        
        self.db = InfluxDBConnection(self)
    
    def run(self):
        while True:
            # this blocks until message received, or timeout occurs
            timeout = 10.0 # value in seconds
            msg = self.connection.recv(timeout=timeout)
            if msg:
                self.db.handle_message(msg)
            self.db.handle_timeout()

# this is a CLI app that reads from network and writes to InfluxDB
def main(args=None):
    dbClient = InfluxDBMsgClient()
    try:
        dbClient.run()
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
        dbClient.connection.stop()

if __name__ == "__main__":
    main()
