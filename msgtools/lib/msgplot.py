#!/usr/bin/env python3
"""
Plot message data in scrolling window
"""
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging

from datetime import datetime
from datetime import timedelta

from collections import namedtuple

# make tuple for line, and have multiple of them in a MsgPlot, as long as their units match and they are from the same message
LineInfo = namedtuple('LineInfo', 'fieldInfo fieldSubindex dataArray timeArray curve ptr1')

start_time = datetime.now().timestamp()
def elapsedSeconds(timestamp):
    if timestamp > start_time:
        return timestamp - start_time
    return timestamp

class MsgPlot(QWidget):
    Paused = QtCore.pyqtSignal(bool)
    AddLineError = QtCore.pyqtSignal(str)
    MAX_LENGTH = 500
    def __init__(self, msgClass, fieldInfo, subindex):
        super(QWidget,self).__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.msgClass = msgClass
        self.pause = 0
        self.lineCount = 0
        self.units = fieldInfo.units
        self.lines = []

        yAxisLabel = fieldInfo.units
        xAxisLabel = "time (s)"
        self.plotWidget = pg.PlotWidget(labels={'left':yAxisLabel,'bottom':xAxisLabel})
        layout.addWidget(self.plotWidget)
        self.plotWidget.addLegend()
        self.addPlot(msgClass, fieldInfo, subindex)

        # set up click handler to pause graph
        self.plotWidget.scene().sigMouseClicked.connect(self.mouseClicked)
        
        # add slider bar to control time scale
        self.timeSlider = QSlider(Qt.Horizontal)
        self.timeSlider.setMinimum(50)
        self.timeSlider.setMaximum(MsgPlot.MAX_LENGTH)
        self.timeSlider.setSingleStep(10)
        self.timeSlider.setPageStep(50)
        layout.addWidget(self.timeSlider)
        
        self.plotWidget.dragEnterEvent = self.dragEnterEvent
        self.plotWidget.dragMoveEvent = self.dragMoveEvent
        self.plotWidget.dropEvent = self.dropEvent
        self.plotWidget.setAcceptDrops(1)
        
    def dragEnterEvent(self, ev):
        # need to accept enter event, or we won't get move event
        ev.accept()

    def dragMoveEvent(self, ev):
        # need to accept move event, or we won't get drop event
        ev.accept()

    def dropEvent(self, ev):
        ev.accept()
        try:
            item = ev.source().currentItem()
            # don't add if it's already there!
            for line in self.lines:
                if item.fieldInfo == line.fieldInfo:
                    self.AddLineError.emit("Line %s already on plot" % item.fieldInfo.name)
                    return
            if type(item.msg) != self.msgClass:
                self.AddLineError.emit("Message %s != %s, cannot add to same plot" % (type(item.msg).__name__, self.msgClass.__name__))
                return
            if item.fieldInfo.units != self.units:
                self.AddLineError.emit("Units %s != %s, not adding to plot" % (item.fieldInfo.units, self.units))
                return
            # index is zero unless the item has something else to use
            fieldIndex = 0
            try:
                fieldIndex = item.index
            except AttributeError:
                pass
            self.addPlot(type(item.msg), item.fieldInfo, fieldIndex)
        except AttributeError:
            pass

    def addPlot(self, msgClass, fieldInfo, subindex):
        lineName = fieldInfo.name
        try:
            if fieldInfo.count != 1:
                lineName += "["+str(self.fieldSubindex)+"]"
        except AttributeError:
            pass
        dataArray = []
        timeArray = []
        ptr1 = 0
        self.useHeaderTime = 0
        curve = self.plotWidget.plot(timeArray, dataArray, name=lineName, pen=(len(self.lines),3))
        lineInfo = LineInfo(fieldInfo, subindex, dataArray, timeArray, curve, ptr1)
        self.lines.append(lineInfo)
        
    def mouseClicked(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pause = not self.pause
        self.Paused.emit(self.pause)

    def addData(self, msg):
        # TODO what to do for things that can't be numerically expressed?  just ascii strings, i guess?
        for line in self.lines:
            newDataPoint = Messaging.getFloat(msg, line.fieldInfo, line.fieldSubindex)
            try:
                timestamp = msg.hdr.GetTime()
                if Messaging.findFieldInfo(msg.hdr.fields, "Time").units == "ms":
                    timestamp = timestamp / 1000.0
                newTime = float(elapsedSeconds(timestamp))
                if newTime != 0:
                    self.useHeaderTime = 1
                if not self.useHeaderTime:
                    newTime = elapsedSeconds(datetime.now().timestamp())
            except AttributeError:
                # if header has no time, fallback to PC time.
                newTime = elapsedSeconds(datetime.now().timestamp())
            
            # add data in the array until MAX_LENGTH is reached, then drop data off start of array
            # such that plot appears to scroll.  The array size is limited to MAX_LENGTH.
            if len(line.dataArray) >= MsgPlot.MAX_LENGTH:
                line.dataArray[:-1] = line.dataArray[1:]  # shift data in the array one sample left
                line.dataArray[-1] = newDataPoint
                line.timeArray[:-1] = line.timeArray[1:]  # shift data in the array one sample left
                line.timeArray[-1] = newTime
            else:
                line.dataArray.append(newDataPoint)
                line.timeArray.append(newTime)

            if not self.pause:
                timeArray = line.timeArray
                dataArray = line.dataArray
                count = self.timeSlider.value()
                if len(line.dataArray) > count:
                    timeArray = timeArray[-count:]
                    dataArray = dataArray[-count:]
                line.curve.setData(timeArray, dataArray)
                line.curve.setPos(line.ptr1, 0)

import msgtools.lib.gui

class MessagePlotGui(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Message Plot 0.1", argv, [], parent)

        vbox = QVBoxLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)
        self.msgPlots = {}
        self.RxMsg.connect(self.ProcessMessage)

        if len(sys.argv) < 1:
            sys.stderr.write('Usage: ' + sys.argv[0] + ' msg1=field1[,field2] [msg2=field1,field2,field3]\n')
            sys.exit(1)
        
        for arg in argv[1:]:
            argComponentList = arg.split("=")
            msgName = argComponentList[0]
            fieldNameList = argComponentList[1]

            self.msgClass = Messaging.MsgClassFromName[msgName]
            
            fieldNames = fieldNameList.split(",")
            firstField = 1
            for fieldName in fieldNames:
                fieldInfo = Messaging.findFieldInfo(self.msgClass.fields, fieldName)
                if fieldInfo != None:
                    if firstField:
                        plot = MsgPlot(self.msgClass, fieldInfo, 0)
                        vbox.addWidget(plot.plotWidget)
                        firstField = 0
                        plotListForID = []
                        if self.msgClass.ID in self.msgPlots:
                            plotListForID = self.msgPlots[self.msgClass.ID]
                        else:
                            self.msgPlots[self.msgClass.ID] = plotListForID
                        plotListForID.append(plot)
                    else:
                        plot.addPlot(self.msgClass, fieldInfo, 0)

    def ProcessMessage(self, msg):
        try:
            if self.msgClass.ID in self.msgPlots:
                plotListForID = self.msgPlots[msg.ID]
                for plot in plotListForID:
                    plot.addData(msg)
        except AttributeError:
            pass

def main(args=None):
    app = QApplication(sys.argv)
    gui = MessagePlotGui(sys.argv)
    gui.show()    
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
