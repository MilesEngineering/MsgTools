#!/usr/bin/env python3
import os
import sys
import argparse
from PyQt5 import QtGui, QtWidgets, QtCore

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

DESCRIPTION='''
    Connects to a MsgSever and listens for BandwidthTest messages. When a message is received
    it is timestamped and sent back.  This app is meant to be used with the BandwidthTester app 
    which sources the BandwidthTest messages and displays results.  The UI also lets you adjust
    % of received messages that are simply dropped.
    '''

class BandwidthTestEcho(msgtools.lib.gui.Gui):
    def __init__(self, parent=None):
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
        args = parser.parse_args()

        msgtools.lib.gui.Gui.__init__(self, "Bandwidth Test Echo 0.1", args, parent)
        
        self.msgCount = 0
        self.dropPercent = 0
        self.rxBytesPerSec = 0
        
        for msgClassName in Messaging.MsgClassFromName:
            if "BandwidthTest" in msgClassName:
                self.bandwidthTestMsgClass = Messaging.MsgClassFromName[msgClassName]
                break
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        vbox = QtWidgets.QVBoxLayout()
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)
        
        dropPercentSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        dropPercentSlider.valueChanged.connect(self.setDropPercent)
        dropPercentLabel = QtWidgets.QLabel()
        dropPercentSlider.valueChanged.connect(lambda newVal: dropPercentLabel.setText(str(newVal)+" % of msgs will be dropped"))
        dropPercentSlider.setMinimum(0)
        dropPercentSlider.setMaximum(100)
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Drop %"))
        hbox.addWidget(dropPercentSlider)
        hbox.addWidget(dropPercentLabel)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Bytes/sec"))
        self.rxBytesPerSecLabel = QtWidgets.QLabel("")
        hbox.addWidget(self.rxBytesPerSecLabel)

        self.displayTimer = QtCore.QTimer(self)
        self.displayTimer.setInterval(1000)
        self.displayTimer.timeout.connect(self.updateDisplay)
        self.displayTimer.start()

    def setDropPercent(self, dropPercent):
        self.dropPercent = dropPercent

    def ProcessMessage(self, msg):
        if type(msg) == self.bandwidthTestMsgClass:
            self.msgCount += 1
            if self.msgCount >= self.dropPercent:
                self.sendBytesFn(msg.rawBuffer().raw)
                self.rxBytesPerSec += msg.hdr.GetDataLength()
            if self.msgCount >= 100:
                self.msgCount = 0

    def updateDisplay(self):
        self.rxBytesPerSecLabel.setText(str(self.rxBytesPerSec))
        self.rxBytesPerSec = 0

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = BandwidthTestEcho()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
