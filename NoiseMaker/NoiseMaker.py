#!/usr/bin/env python3
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *
from PySide.QtCore import QTimer

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class MsgInspector(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Noise Maker 0.1", argv, parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ShowMessage)
        
        self.currentTime = 0
        
        self.msgTimer = QTimer(self)
        self.msgTimer.setInterval(10)
        self.msgTimer.timeout.connect(self.msgTImeout)

        self.startStop = QPushButton(self)
        self.startStop.setText('Stop')
        self.startStop.clicked.connect(self.startStopFn)
        self.setCentralWidget(self.startStop)
        
        # find a few messages to send at specified rates
        period = 300
        self.fieldNumber = 0
        self.msgPeriod = {}
        self.msgTxTime = {}
        for msgName in Messaging.MsgClassFromName:
            print("found message " + msgName)
            self.msgPeriod[msgName] = period
            period = period + 200
            self.msgTxTime[msgName] = 0
        
        self.msgTimer.start()
        
    def startStopFn(self):
        if self.msgTimer.isActive():
            self.msgTimer.stop()
            self.startStop.setText('Start')
        else:
            self.msgTimer.start()
            self.startStop.setText('Stop')
    
    def msgTImeout(self):
        self.currentTime += 10
        for msgName in self.msgTxTime:
            if self.currentTime > self.msgTxTime[msgName]:
                msgClass = Messaging.MsgClassFromName[msgName]
                self.msgTxTime[msgName] = self.currentTime + self.msgPeriod[msgName]
                self.sendMsg(msgClass)
                
    def sendMsg(self, msgClass):
        msg = msgClass.Create()
        Messaging.hdr.SetTime(msg, self.currentTime)
        for fieldInfo in msgClass.fields:
            if fieldInfo.units == 'ASCII':
                Messaging.set(msg, fieldInfo, 's'+str(self.fieldNumber))
                self.fieldNumber += 1
                if self.fieldNumber > 255:
                    self.fieldNumber = 0
            else:
                if(fieldInfo.count == 1):
                    Messaging.set(msg, fieldInfo, self.fieldNumber)
                    self.fieldNumber += 1
                    if self.fieldNumber > 255:
                        self.fieldNumber = 0
                    for bitInfo in fieldInfo.bitfieldInfo:
                        Messaging.set(msg, bitInfo, self.fieldNumber)
                        self.fieldNumber += 1
                    if self.fieldNumber > 255:
                        self.fieldNumber = 0
                else:
                    for i in range(0,fieldInfo.count):
                        Messaging.set(msg, fieldInfo, self.fieldNumber, i)
                        self.fieldNumber += 1
                        if self.fieldNumber > 255:
                            self.fieldNumber = 0
        self.sendFn(msg.raw)

    def ShowMessage(self, msg):
        print('rx!')

# main starts here
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
