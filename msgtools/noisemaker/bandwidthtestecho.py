#!/usr/bin/env python3
import sys
from PyQt5 import QtGui, QtWidgets, QtCore

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

class BandwidthTestEcho(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Bandwidth Test Echo 0.1", argv, [], parent)
        
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
    msgApp = BandwidthTestEcho(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
