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
    def __init__(self, dbname='messages', hostname='localhost', port=8086, username='root', password='root'):
        self.db = InfluxDBClient(hostname, port, username, password, dbname)
        
    @staticmethod
    def GetDBValue(msg, fieldInfo, index=0):
        # what to do for arrays?
        val = Messaging.get(msg, fieldInfo, index)
        if fieldInfo.type == 'int':
            val = int(val)
        elif fieldInfo.type == 'float':
            val = float(val)
        #elif fieldInfo.type == 'Enum'
        #    what?
        return val

    def send_message(self, msg):
        # need to use msg time from header once it's 64-bit UTC time!
        now = datetime.datetime.utcnow()

        pointValues = {
                "time": str(now),
                "measurement": msg.MsgName(),
                'fields':  {},
                'tags': {
                    "deviceID": "unknown", # need to base this on something about the hardware we're talking to
                },
            }
        
        msgClass = type(msg)
        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                if len(fieldInfo.bitfieldInfo) == 0:
                    pointValues['fields'][fieldInfo.name] = InfluxDBConnection.GetDBValue(msg, fieldInfo)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        pointValues['fields'][bitInfo.name] = InfluxDBConnection.GetDBValue(msg, bitInfo)
            # leave out arrays until we figure out how to handle them
            #else:
            #    arrayList = []
            #    for i in range(0,fieldInfo.count):
            #        arrayList.append(InfluxDBConnection.GetDBValue(msg, fieldInfo, i))
            #    pointValues['fields'][fieldInfo.name] = arrayList

        #print("Create a retention policy")
        #retention_policy = 'awesome_policy'
        #client.create_retention_policy(retention_policy, '3d', 3, default=True)
        self.db.write_points([pointValues]) #, retention_policy=retention_policy)

# this is client that reads from network, and writes to InfluxDB
class InfluxDBMsgClient:
    def __init__(self):
        self.msgLib = Messaging(None, 0, "NetworkHeader")

        self.connection = SynchronousMsgClient(Messaging.hdr)
        # say my name
        connectMsg = self.msgLib.Messages.Network.Connect()
        connectMsg.SetName("InfluxDB")
        self.connection.send_message(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = self.msgLib.Messages.Network.MaskedSubscription()
        self.connection.send_message(subscribeMsg)

        self.db = InfluxDBConnection()
    
    def run(self):
        while True:
            # this blocks until message received, or timeout occurs
            timeout = 10.0 # value in seconds
            hdr = self.connection.get_message(timeout)
            if hdr:
                msg = self.msgLib.MsgFactory(hdr)
                self.db.send_message(msg)

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
