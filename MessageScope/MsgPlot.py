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
        #self.win = pg.GraphicsWindow()
        #self.win.setWindowTitle(msgClass.MsgName())
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
        xAxisLabel = "time (count)"
        self.plotWidget = pg.PlotWidget()
        #self.myPlot = self.win.addPlot(viewBox=vb, labels={'left':  yAxisLabel, 'bottom': xAxisLabel})
        self.myPlot = self.plotWidget
        self.dataArray = []
        self.curve = self.myPlot.plot(self.dataArray)
        self.ptr1 = 0

    def addData(self, message_buffer):
        newDataPoint = float(Messaging.get(message_buffer, self.fieldInfo, self.fieldSubindex))
        # TODO do something to get time on the X axis!
        newTime = float(Messaging.hdr.GetTime(message_buffer)/1000.0)
        # add data in the array until MAX_LENGTH is reached, then drop data off start of array
        # such that plot appears to scroll.  The array size is limited to MAX_LENGTH.
        if len(self.dataArray) >= MsgPlot.MAX_LENGTH:
            self.dataArray[:-1] = self.dataArray[1:]  # shift data in the array one sample left
            self.dataArray[-1] = newDataPoint
        else:
            self.dataArray.append(newDataPoint)

        global pause
        if not pause:
            self.ptr1 += 1
            self.curve.setData(self.dataArray)
            self.curve.setPos(self.ptr1, 0)

sys.path.append(srcroot+"/../obj/CodeGenerator/Python/Test")
from TestMsg1 import TestMsg1

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
