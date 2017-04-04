#!/usr/bin/env python3
"""
Plot message data in scrolling window
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

import sys
# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/../MsgApp")
from Messaging import Messaging

from datetime import datetime
from datetime import timedelta

start_time = datetime.now()

def elapsedSeconds():
   dt = datetime.now() - start_time
   seconds = float(dt.days * 24 * 60 * 60 + dt.seconds) + dt.microseconds / 1000000.0
   return seconds

pause = 0

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        
    def mouseClickEvent(self, ev):
        global pause
        if ev.button() == QtCore.Qt.LeftButton:
            pause = not pause

class MsgPlot:
    MAX_LENGTH = 100
    def __init__(self, msgClass, fieldInfo, subindex):
        self.msgClass = msgClass
        self.fieldInfo = fieldInfo
        self.fieldSubindex = subindex

        vb = CustomViewBox() # this is no longer used since we don't use self.win.addPlot
        # anymore, so now left click to pause no longer works :(
        
        yAxisLabel = fieldInfo.name
        try:
            if fieldInfo.count != 1:
                yAxisLabel += "["+str(self.fieldSubindex)+"]"
        except AttributeError:
            pass
        yAxisLabel += "  (" + fieldInfo.units+")"
        xAxisLabel = "time (s)"
        self.plotWidget = pg.PlotWidget()
        self.myPlot = self.plotWidget
        self.dataArray = []
        self.timeArray = []
        self.curve = self.myPlot.plot(self.timeArray, self.dataArray)
        self.ptr1 = 0
        self.useHeaderTime = 0

    def addData(self, message_buffer):
        # TODO what to do for things that can't be numerically expressed?  just ascii strings, i guess?
        newDataPoint = Messaging.getFloat(message_buffer, self.fieldInfo, self.fieldSubindex)
        try:
            newTime = float(Messaging.hdr.GetTime(message_buffer)/1000.0)
            if newTime != 0:
                self.useHeaderTime = 1
            if not self.useHeaderTime:
                newTime = elapsedSeconds()
        except AttributeError:
            # if header has no time, fallback to PC time.
            newTime = elapsedSeconds()
        
        # add data in the array until MAX_LENGTH is reached, then drop data off start of array
        # such that plot appears to scroll.  The array size is limited to MAX_LENGTH.
        if len(self.dataArray) >= MsgPlot.MAX_LENGTH:
            self.dataArray[:-1] = self.dataArray[1:]  # shift data in the array one sample left
            self.dataArray[-1] = newDataPoint
            self.timeArray[:-1] = self.timeArray[1:]  # shift data in the array one sample left
            self.timeArray[-1] = newTime
        else:
            self.dataArray.append(newDataPoint)
            self.timeArray.append(newTime)

        global pause
        if not pause:
            self.curve.setData(self.timeArray, self.dataArray)
            self.curve.setPos(self.ptr1, 0)

try:
    sys.path.append(srcroot+"/../obj/CodeGenerator/Python/Test")
    from TestMsg1 import TestMsg1
except:
    pass

def onTimeout():
    messageBuffer = TestMessage1.Create()
    newDataPoint =  np.random.normal()
    Messaging.set(messageBuffer, TestMessage1.fields[1], newDataPoint, 0)
    msgPlot.addData(messageBuffer)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    
    msgdir = srcroot+"/../obj/CodeGenerator/Python/"
    msgLib = Messaging(msgdir, 0)
    
    msgPlot = MsgPlot(TestMessage1, TestMessage1.fields[1], 0)
    
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(onTimeout)
    timer.start(50)
    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
