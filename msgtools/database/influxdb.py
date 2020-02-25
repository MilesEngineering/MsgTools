#!/usr/bin/python3
import os

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging
import msgtools.console.client

from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
import datetime

# this allows sending Messages as data to an InfluxDB database
class InfluxDBConnection:
    MAX_POINTS = 128
    def __init__(self, msgClient, dbname='messages', hostname='localhost', port=8086, username='root', password='root'):
        self.hostname = hostname
        self.port = port
        self.db = InfluxDBClient(host=hostname, port=port, username=username, password=password, database=dbname)
        self.msgClient = msgClient
        self.cookie = 0
        
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
            self.dataResultOffset = min(self.dataValueInfo.offset+self.dataTimestampInfo.offset)
    
    @staticmethod
    def FormattedTime(floatTime):
        return str(int(floatTime * 1e9))

    @staticmethod
    def GetDBValue(msg, fieldInfo, index=0):
        # what to do for arrays?
        val = Messaging.get(msg, fieldInfo, index)
        if fieldInfo.type == 'int':
            val = int(val)
        elif fieldInfo.type == 'float':
            val = float(val)
        return val

    def handle_message(self, msg):
        if msg.MsgName().startswith("Network"):
            if msg.MsgName() == "Network.History.GetData":
                self.handle_query(msg)
        else:
            self.store_message(msg)
    
    def store_message(self, msg):
        try:
            timeVal = msg.hdr.GetTime()
            timeInfo = Messaging.findFieldInfo(msg.hdr.fields, "Time")
            maxTime = timeInfo.maxVal
            # if it's not big enough to be an absolute timestamp, give up on using it and just use current time
            if maxTime != "DBL_MAX" and (maxTime == 'FLT_MAX' or float(maxTime) <= 2**32):
                raise AttributeError
            if timeInfo.units == "ms":
                timeVal = timeVal / 1000.0
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
                    dbJson['fields'][fieldInfo.name] = InfluxDBConnection.GetDBValue(msg, fieldInfo)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        dbJson['fields'][bitInfo.name] = InfluxDBConnection.GetDBValue(msg, bitInfo)
            else:
                # flatten arrays
                for i in range(0,fieldInfo.count):
                    dbJson['fields'][fieldInfo.name+"_"+str(i)] = InfluxDBConnection.GetDBValue(msg, fieldInfo, i)

        #print("Create a retention policy")
        #retention_policy = 'awesome_policy'
        #client.create_retention_policy(retention_policy, '3d', 3, default=True)
        self.db.write_points([dbJson]) #, retention_policy=retention_policy)

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

# this is client that reads from network, and writes to InfluxDB
class InfluxDBMsgClient:
    def __init__(self):
        Messaging.LoadAllMessages()

        self.connection = msgtools.console.client(Messaging.hdr)
        # say my name
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName("InfluxDB")
        self.connection.send_message(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
        self.connection.send_message(subscribeMsg)

        self.db = InfluxDBConnection(self)
    
    def run(self):
        while True:
            # this blocks until message received, or timeout occurs
            timeout = 10.0 # value in seconds
            hdr = self.connection.get_message(timeout)
            if hdr:
                msg = Messaging.MsgFactory(hdr)
                self.db.handle_message(msg)

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
