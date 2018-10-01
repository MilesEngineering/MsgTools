#!/usr/bin/python3

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging

from msgtools.console.SynchronousMsgClient import SynchronousMsgClient

from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
import datetime

# this allows sending Messages as data to an InfluxDB database
class InfluxDBConnection:
    MAX_POINTS = 100
    def __init__(self, msgClient, dbname='messages', hostname='localhost', port=8086, username='root', password='root'):
        self.hostname = hostname
        self.port = port
        self.db = InfluxDBClient(hostname, port, username, password, dbname)
        self.msgClient = msgClient
        self.cookie = 0
    
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
        #elif fieldInfo.type == 'Enum'
        #    what?  int value, string?
        return val

    def handle_message(self, msg):
        if msg.MsgName().startsWith("Network"):
            if msg.MsgName() == "Network.History.GetData":
                self.handle_query(msg)
        else:
            self.store_message(msg)
    
    def store_message(self, msg):
        try:
            timeVal = msg.hdr.GetTime()
            timeInfo = Messaging.findFieldInfo(msg.hdr.fields, "Time")
            # if it's not big enough to be an absolute timestamp, give up on using it and just use current time
            if float(timeInfo.maxVal) <= 2**32:
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
            # leave out arrays until we figure out how to handle them
            #else:
            #    arrayList = []
            #    for i in range(0,fieldInfo.count):
            #        arrayList.append(InfluxDBConnection.GetDBValue(msg, fieldInfo, i))
            #    dbJson['fields'][fieldInfo.name] = arrayList

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

        # send query to database, get result
        result = self.db.query(dbquery)

        # output results
        resultMsg = Messaging.Messages.Network.History.Result()
        resultMsg.SetCookie(self.cookie)
        resultCount = f(result)
        resultMsg.SetResultCount(resultCount)
        resultMsg.SetQuery(msgquery)
        self.msgClient.send_message(resultMsg)

        dataInfo = Messaging.findFieldInfo(Messaging.Messages.Network.History.Data, "Data")
        maxDataPerMsg = dataInfo.count
        resultNumber = 0
        for something in result:
            dataMsg = Messaging.Messages.Network.History.Data()
            dataMsg.SetCookie(self.cookie)
            dataMsg.SetResultNumber(resultNumber)
            dataRange = min(maxDataPerMsg, tilEndOfResults)
            for index in range(0, dataRange,2):
                dataMsg.SetData(time(something), index)
                dataMsg.SetData(value(something), index+1)
            # truncate message buffer to actual amount of data
            dataMsg.hdr.SetDataLength(dataInfo.offset + dataInfo.size * dataRange)
            self.msgClient.send_message(dataMsg)
            resultNumber += 1

        # increment cookie so the next query's results are easy to tell apart from out query results
        # especially useful if two clients query at almost the same time!
        self.cookie += 1

# this is client that reads from network, and writes to InfluxDB
class InfluxDBMsgClient:
    def __init__(self):
        Messaging.LoadAllMessages()

        self.connection = SynchronousMsgClient(Messaging.hdr)
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
