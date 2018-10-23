#!/usr/bin/env python3
import os
import sys
import argparse
from PyQt5 import QtGui, QtWidgets, QtCore
import time

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

DESCRIPTION='''
    BandwidthTester is designed to work with the BandWidthTestEcho utility.  It connects to a
    MsgServer and sends Bandwidth test messages, listening for echo responses with timestamps.
    Basic stats are provided to allow you rough order of throughput.  Python is not very stable
    when it comes to timing and multi-threaded operations so expect some margin of error in your 
    results.
'''

class BandwidthTester(msgtools.lib.gui.Gui):
    startTime = int(time.time() * 1000)
    def __init__(self, parent=None):
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
        args = parser.parse_args()

        msgtools.lib.gui.Gui.__init__(self, "Bandwidth Tester 0.1", args, parent)
        
        self.lastTxSequence = 0
        self.lastRxSequence = 0
        self.txMsgCount = 0
        self.txLen = 0
        self.txByteCount = 0
        self.rxByteCount = 0
        self.rxBytesPerSec = 0
        self.txBytesPerSec = 0
        self.totalLatency = 0
        self.latencySamples = 0
        
        for msgClassName in Messaging.MsgClassFromName:
            if "BandwidthTest" in msgClassName:
                self.bandwidthTestMsgClass = Messaging.MsgClassFromName[msgClassName]
                break
        self.maxSeq = int(self.bandwidthTestMsgClass.GetSequenceNumber.maxVal)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.msgTimer = QtCore.QTimer(self)
        self.msgTimer.setInterval(10)
        self.msgTimer.timeout.connect(self.msgTimeout)

        self.displayTimer = QtCore.QTimer(self)
        self.displayTimer.setInterval(1000)
        self.displayTimer.timeout.connect(self.updateDisplay)
        self.displayTimer.start()

        vbox = QtWidgets.QVBoxLayout()
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)
        
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Tx bytes"))
        self.txByteCountLabel = QtWidgets.QLabel()
        hbox.addWidget(self.txByteCountLabel)
        hbox.addWidget(QtWidgets.QLabel("Rx bytes"))
        self.rxByteCountLabel = QtWidgets.QLabel()
        hbox.addWidget(self.rxByteCountLabel)

        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Tx bytes/sec"))
        self.txBytesPerSecLabel = QtWidgets.QLabel()
        hbox.addWidget(self.txBytesPerSecLabel)
        hbox.addWidget(QtWidgets.QLabel("Rx bytes/sec"))
        self.rxBytesPerSecLabel = QtWidgets.QLabel()
        hbox.addWidget(self.rxBytesPerSecLabel)
        
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        self.latencyLabel = QtWidgets.QLabel()
        hbox.addWidget(QtWidgets.QLabel("Round-trip latency"))
        hbox.addWidget(self.latencyLabel)
        hbox.addWidget(QtWidgets.QLabel("ms"))

        clearBtn = QtWidgets.QPushButton(self)
        clearBtn.setText('Clear')
        clearBtn.clicked.connect(self.clearStats)
        vbox.addWidget(clearBtn)
        
        timerSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        timerSlider.valueChanged.connect(self.msgTimer.setInterval)
        timerLabel = QtWidgets.QLabel()
        timerSlider.valueChanged.connect(lambda newVal: timerLabel.setText(str(newVal)+" ms"))
        timerSlider.setMinimum(10)
        timerSlider.setMaximum(1000)
        timerSlider.setValue(500)
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Timer (ms)"))
        hbox.addWidget(timerSlider)
        hbox.addWidget(timerLabel)
        
        txMsgCountSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        txMsgCountSlider.valueChanged.connect(self.setTxMsgCount)
        msgCountLabel = QtWidgets.QLabel()
        txMsgCountSlider.valueChanged.connect(lambda newVal: msgCountLabel.setText(str(newVal)+" msgs"))
        txMsgCountSlider.setMinimum(1)
        txMsgCountSlider.setMaximum(100)
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Msg Count"))
        hbox.addWidget(txMsgCountSlider)
        hbox.addWidget(msgCountLabel)

        txDataLenSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        txDataLenSlider.valueChanged.connect(self.setTxLen)
        txDataLenLabel = QtWidgets.QLabel()
        txDataLenSlider.valueChanged.connect(lambda newVal: txDataLenLabel.setText(str(newVal*int(self.bandwidthTestMsgClass.GetTestData.size)+int(self.bandwidthTestMsgClass.GetTestData.offset))+" bytes"))
        txDataLenSlider.setMinimum(0)
        txDataLenSlider.setMaximum(int(self.bandwidthTestMsgClass.GetTestData.count))
        txDataLenSlider.setValue(3)
        hbox = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(QtWidgets.QLabel("Msg Len"))
        hbox.addWidget(txDataLenSlider)
        hbox.addWidget(txDataLenLabel)

        self.startStop = QtWidgets.QPushButton(self)
        self.startStop.setText('Stop')
        self.startStop.clicked.connect(self.startStopFn)
        vbox.addWidget(self.startStop)
        
        self.msgTimer.start()
        
    def startStopFn(self):
        if self.msgTimer.isActive():
            self.msgTimer.stop()
            self.startStop.setText('Start')
        else:
            self.msgTimer.start()
            self.startStop.setText('Stop')
    
    def setTxMsgCount(self, txCount):
        self.txMsgCount = txCount

    def setTxLen(self, txLen):
        self.txLen = txLen

    def msgTimeout(self):
        bytesTransmitted = 0
        for i in range(0, self.txMsgCount):
            msg = self.bandwidthTestMsgClass()
            self.lastTxSequence += 1
            if self.lastTxSequence > self.maxSeq:
                self.lastTxSequence = 0
            msg.SetSequenceNumber(self.lastTxSequence)
            msgLen = int(msg.SetTestData.offset) + int(msg.SetTestData.size)*self.txLen
            if(self.txLen >= 1):
                sendTime = int(time.time() * 1000)-self.startTime
                msg.SetTestData(sendTime,0)
            msg.hdr.SetDataLength(msgLen)
            self.txByteCount += msgLen
            self.txBytesPerSec += msgLen
            self.SendMsg(msg)
        self.txByteCountLabel.setText(str(self.txByteCount))

    def ProcessMessage(self, msg):
        if type(msg) == self.bandwidthTestMsgClass:
            desiredSeq = self.lastRxSequence+1
            if desiredSeq > self.maxSeq:
                desiredSeq = 0
            if msg.GetSequenceNumber() == desiredSeq:
                if msg.hdr.GetDataLength() >= int(msg.GetTestData.offset)+int(msg.GetTestData.size):
                    sendTime = msg.GetTestData(0)
                    recvTime = int(time.time() * 1000)-self.startTime
                    latency = recvTime - sendTime
                    self.totalLatency += latency
                    self.latencySamples += 1
                self.rxByteCount += msg.hdr.GetDataLength()
                self.rxBytesPerSec += msg.hdr.GetDataLength()
            else:
                print("ERROR!  Got sequence " + str(msg.GetSequenceNumber()) + ", but wanted " + str(self.lastRxSequence))
            self.lastRxSequence = msg.GetSequenceNumber()
            self.rxByteCountLabel.setText(str(self.rxByteCount))
    
    def clearStats(self):
        self.txByteCount = 0
        self.rxByteCount = 0
        self.totalLatency = 0
        self.latencySamples = 0
        self.txByteCountLabel.setText("0")
        self.rxByteCountLabel.setText("0")
        self.latencyLabel.setText("")

    
    def updateDisplay(self):
        self.rxBytesPerSecLabel.setText(str(self.rxBytesPerSec))
        self.txBytesPerSecLabel.setText(str(self.txBytesPerSec))
        if self.latencySamples > 0:
            self.latencyLabel.setText('%.2f' % (self.totalLatency / self.latencySamples))
        else:
            self.latencyLabel.setText("undef")
        self.rxBytesPerSec = 0
        self.txBytesPerSec = 0
        self.totalLatency = 0
        self.latencySamples = 0

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = BandwidthTester()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
