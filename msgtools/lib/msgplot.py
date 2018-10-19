#!/usr/bin/env python3
"""
Plot message data in scrolling window
"""
import sys
import argparse

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
    class PlotError(Exception):
        pass

    class NewPlotError(PlotError):
        pass

    Paused = QtCore.pyqtSignal(bool)
    AddLineError = QtCore.pyqtSignal(str)
    MAX_LENGTH = 500
    def __init__(self, msgClass, fieldName):
        super(QWidget,self).__init__()
        
        newFieldName, fieldIndex = MsgPlot.split_fieldname(fieldName)
        fieldInfo = Messaging.findFieldInfo(msgClass.fields, newFieldName)
        if fieldInfo == None:
            raise MsgPlot.PlotError("Invalid field %s for message %s" % (newFieldName, msgClass.MsgName()))

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
        self.addLine(msgClass, fieldName)

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

    @staticmethod
    def split_fieldname(fieldName):
        fieldIndex = None
        if '[' in fieldName  and ']' in fieldName:
            splits = fieldName.split('[')
            splits[1] = splits[1].replace(']','')
            fieldName = splits[0]
            fieldIndex = int(splits[1])
        return (fieldName, fieldIndex)

    def dragEnterEvent(self, ev):
        # need to accept enter event, or we won't get move event
        ev.accept()

    def dragMoveEvent(self, ev):
        # need to accept move event, or we won't get drop event
        ev.accept()

    def dropEvent(self, ev):
        ev.accept()
        item = ev.source().currentItem()
        try:
            self.addLine(type(item.msg), item.fieldName)
        except MsgPlot.PlotError as e:
            self.AddLineError.emit(str(e))

    def addLine(self, msgClass, fieldName):
        fieldName, fieldIndex = MsgPlot.split_fieldname(fieldName)
        fieldInfo = Messaging.findFieldInfo(msgClass.fields, fieldName)
        if fieldInfo == None:
            raise MsgPlot.PlotError("Invalid field %s for message %s" % (fieldName, msgClass.MsgName()))
        
        if fieldInfo.units == "ASCII":
            raise MsgPlot.PlotError("Cannot plot %s.%s, it is a string" % (msgClass.MsgName(), fieldName))
        
        # don't add if it's already there!
        for line in self.lines:
            if fieldInfo == line.fieldInfo and fieldIndex == line.fieldSubindex:
                name = fieldInfo.name
                if fieldInfo.count > 1:
                    name = "%s[%d]" % (name, fieldIndex)
                raise MsgPlot.PlotError("Line %s already on plot" % name)
        if msgClass != self.msgClass:
            raise MsgPlot.NewPlotError("Message %s != %s, cannot add to same plot" % (msgClass.__name__, self.msgClass.__name__))
        if fieldInfo.units != self.units:
            raise MsgPlot.NewPlotError("Units %s != %s, not adding to plot" % (fieldInfo.units, self.units))
        
        if fieldIndex != None:
            self._addLine(msgClass, fieldInfo, fieldIndex)
        elif fieldInfo.count == 1:
            self._addLine(msgClass, fieldInfo, 0)
        else:
            dups = []
            for fieldIndex in range(0, fieldInfo.count):
                duplicate = False
                for line in self.lines:
                    if fieldInfo == line.fieldInfo and fieldIndex == line.fieldSubindex:
                        dups.append(fieldIndex)
                        duplicate = True
                        break
                if not duplicate:
                    self._addLine(msgClass, fieldInfo, fieldIndex)
            if len(dups) > 0:
                if len(dups) == 1:
                    s = ' '+str(dups[0])
                elif len(dups) == fieldInfo.count:
                    s = 's %d-%d' % (0, fieldInfo.count)
                else:
                    s = 's '
                    for d in dups:
                        s += '%s,' % d
                raise MsgPlot.PlotError("Line%s already on plot" % s)

    def _addLine(self, msgClass, fieldInfo, fieldIndex):
        lineName = fieldInfo.name
        try:
            if fieldInfo.count != 1:
                lineName += "["+str(fieldIndex)+"]"
        except:
            pass
        dataArray = []
        timeArray = []
        ptr1 = 0
        self.useHeaderTime = 0
        curve = self.plotWidget.plot(timeArray, dataArray, name=lineName, pen=(len(self.lines)))
        lineInfo = LineInfo(fieldInfo, fieldIndex, dataArray, timeArray, curve, ptr1)
        self.lines.append(lineInfo)
        
    def mouseClicked(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pause = not self.pause
        self.Paused.emit(self.pause)

    def addData(self, msg):
        # TODO what to do for things that can't be numerically expressed?  just ascii strings, i guess?
        for line in self.lines:
            try:
                newDataPoint = Messaging.getFloat(msg, line.fieldInfo, line.fieldSubindex)
            except ValueError:
                print("ERROR! Plot of %s.%s cannot accept value %s" % (
                    self.msgClass.MsgName(),
                    line.fieldInfo.name,
                    Messaging.get(msg, line.fieldInfo, line.fieldSubindex)))
                continue
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

    @staticmethod
    def plotFactory(msgPlot, new_plot, msgClass, fieldNames):
        if len(fieldNames) == 0:
            fieldNames = [fieldInfo.name for fieldInfo in msgClass.fields]
        for fieldName in fieldNames:
            # if there's a plot widget, try adding a line to it
            if msgPlot != None:
                try:
                    msgPlot.addLine(msgClass, fieldName)
                except MsgPlot.NewPlotError as e:
                    # if error on adding to existing plot, then make a new plot
                    msgPlot = None
                except MsgPlot.PlotError as e:
                    print(str(e))
            
            # make new plot
            if msgPlot == None:
                try:
                    msgPlot = MsgPlot(msgClass, fieldName)
                    new_plot(msgPlot)
                except MsgPlot.PlotError as e:
                    print(str(e))
        return msgPlot


import msgtools.lib.gui

class MessagePlotGui(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        parser = argparse.ArgumentParser(description="Tool to plot message fields")
        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
        args=parser.parse_args([arg for arg in argv[1:] if not '=' in arg])

        msgtools.lib.gui.Gui.__init__(self, "Message Plot 0.1", args, parent)

        self.plotlayout = QVBoxLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(self.plotlayout)
        self.setCentralWidget(centralWidget)
        self.msgPlots = {}
        self.RxMsg.connect(self.ProcessMessage)

        if len(sys.argv) < 2:
            sys.stderr.write('Usage: ' + sys.argv[0] + ' msg1=field1[,field2] [msg2=field1,field2,field3]\n')
            sys.exit(1)
        
        msgPlot = None
        for arg in argv[1:]:
            argComponentList = arg.split("=")
            msgName = argComponentList[0]
            fieldNameList = argComponentList[1]

            try:
                msgClass = Messaging.MsgClassFromName[msgName]
            except KeyError:
                print("ERROR!  Invalid message name " + msgName)
                continue
            
            if fieldNameList:
                fieldNames = fieldNameList.split(",")
            else:
                fieldNames = []
            msgPlot = MsgPlot.plotFactory(msgPlot, self.newPlot, msgClass, fieldNames)

    def newPlot(self, plot):
        self.plotlayout.addWidget(QLabel(plot.msgClass.MsgName()))
        self.plotlayout.addWidget(plot)
        if not plot.msgClass.ID in self.msgPlots:
            self.msgPlots[plot.msgClass.ID] = []
        self.msgPlots[plot.msgClass.ID].append(plot)
    
    def ProcessMessage(self, msg):
        if msg.ID in self.msgPlots:
            plotListForID = self.msgPlots[msg.ID]
            for plot in plotListForID:
                plot.addData(msg)

def main(args=None):
    app = QApplication(sys.argv)
    gui = MessagePlotGui(sys.argv)
    gui.show()    
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
