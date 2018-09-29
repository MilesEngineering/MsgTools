#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QTimer

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

DESCRIPTION='''
    Noisemaker is a utility for generating message traffic.  Messages are roughly 
    staggered with a constant delta between each message, triggered at a rate 33Hz rate.
    Python's built in timing is highly unstable.  Timing won't be extremeley precise.
'''

class NoiseMaker(msgtools.lib.gui.Gui):
    def __init__(self, parent=None):

        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('msgs', nargs='*', help='''
            One or more messages that you wish to send.  This entire list is sent each 
            time the message period is up.  Network messages are ignored.  By default we 
            send all known messages.''')
        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
        args = parser.parse_args()

        msgtools.lib.gui.Gui.__init__(self, "Noise Maker 0.1", args, parent)
        
        self.timeInfo = Messaging.findFieldInfo(Messaging.hdr.fields, "Time")
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)
        
        self.currentTime = 0
        
        self.msgTimer = QTimer(self)
        self.msgTimer.setInterval(10)
        self.msgTimer.timeout.connect(self.msgTimeout)

        self.startStop = QtWidgets.QPushButton(self)
        self.startStop.setText('Stop')
        self.startStop.clicked.connect(self.startStopFn)
        self.setCentralWidget(self.startStop)
        
        # check if user specified which messages we should output
        msgs = args.msgs
        
        # find a few messages to send at specified rates
        period = 0.3
        self.fieldNumber = 0
        self.msgPeriod = {}
        self.msgTxTime = {}
        for msgName in Messaging.MsgClassFromName:
            if not msgName.startswith("Network"):
                if len(msgs) > 0 and msgName not in msgs:
                    continue
                print("found message " + msgName)
                self.msgPeriod[msgName] = period
                period = period + 0.020
                self.msgTxTime[msgName] = 0
       
        self.msgTimer.start()
        
    def startStopFn(self):
        if self.msgTimer.isActive():
            self.msgTimer.stop()
            self.startStop.setText('Start')
        else:
            self.msgTimer.start()
            self.startStop.setText('Stop')
    
    def msgTimeout(self):
        self.currentTime = datetime.now().timestamp()
        for msgName in self.msgTxTime:
            if self.currentTime > self.msgTxTime[msgName]:
                msgClass = Messaging.MsgClassFromName[msgName]
                self.msgTxTime[msgName] = self.currentTime + self.msgPeriod[msgName]
                self.sendMsg(msgClass)
    
    def fieldValue(self, fieldInfo):
        minVal = 0
        maxVal = 255
        try:
            minVal = float(fieldInfo.minVal)
            maxVal = float(fieldInfo.maxVal)
        except (AttributeError, ValueError):
            minVal = 0
            maxVal = 255
        self.fieldNumber += 1
        if self.fieldNumber > 255:
            self.fieldNumber = 0
        # go from 10% below range to 10% above range
        bottom = minVal - 0.1 * (maxVal-minVal)
        range = 1.2 * (maxVal-minVal) 
        scale = self.fieldNumber / (255.0)
        return bottom + range * scale
                
    def sendMsg(self, msgClass):
        msg = msgClass()
        if self.timeInfo.units:
            hdr = Messaging.hdr(msg.rawBuffer())
            #Messaging.set(hdr, self.timeInfo, self.currentTime)
            t = self.currentTime
            maxTime = self.timeInfo.maxVal
            if maxTime != "DBL_MAX" and (maxTime == 'FLT_MAX' or float(maxTime) <= 2**32):
                t = (datetime.fromtimestamp(self.currentTime) - datetime.fromtimestamp(self.currentTime).replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            if self.timeInfo.units == "ms":
                t = t * 1000.0
            if self.timeInfo.type == "int":
                t = int(t)
            hdr.SetTime(t)

        for fieldInfo in msgClass.fields:
            if fieldInfo.units == 'ASCII':
                Messaging.set(msg, fieldInfo, 's'+str(self.fieldValue(fieldInfo)))
            else:
                if(fieldInfo.count == 1):
                    Messaging.set(msg, fieldInfo, str(self.fieldValue(fieldInfo)))
                    for bitInfo in fieldInfo.bitfieldInfo:
                        Messaging.set(msg, bitInfo, str(self.fieldValue(bitInfo)))
                else:
                    for i in range(0,fieldInfo.count):
                        Messaging.set(msg, fieldInfo, self.fieldValue(fieldInfo), i)
        self.SendMsg(msg)

    def ProcessMessage(self, msg):
        pass

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = NoiseMaker()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
