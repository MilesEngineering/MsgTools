#!/usr/bin/env python3
import sys
from PyQt5 import QtGui, QtWidgets, QtCore

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class BandwidthTestEcho(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Bandwidth Test Echo 0.1", argv, [], parent)
        
        self.msgCount = 0
        self.dropPercent = 0
        
        self.bandwidthTestMsgClass = Messaging.MsgClassFromName["Debug.BandwidthTest"]
        
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

    def setDropPercent(self, dropPercent):
        self.dropPercent = dropPercent

    def ProcessMessage(self, msg):
        if type(msg) == self.bandwidthTestMsgClass:
            self.msgCount += 1
            if self.msgCount >= self.dropPercent:
                self.sendBytesFn(msg.rawBuffer())
            if self.msgCount >= 100:
                self.msgCount = 0

# main starts here
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    msgApp = BandwidthTestEcho(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
