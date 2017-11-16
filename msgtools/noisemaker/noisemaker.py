#!/usr/bin/env python3
import sys
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

class NoiseMaker(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Noise Maker 0.1", argv, [], parent)
        
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
        
        # find a few messages to send at specified rates
        period = 300
        self.fieldNumber = 0
        self.msgPeriod = {}
        self.msgTxTime = {}
        for msgName in Messaging.MsgClassFromName:
            if not msgName.startswith("Network"):
                #print("found message " + msgName)
                self.msgPeriod[msgName] = period
                period = period + 20
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
        self.currentTime += 10
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
        try:
            hdr = Messaging.hdr(msg.rawBuffer())
            hdr.SetTime(self.currentTime)
        except AttributeError:
            pass
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
    msgApp = NoiseMaker(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
