#!/usr/bin/env python3
"""
Plot message data in scrolling window
"""
import os
import sys
import argparse

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging, FieldInfo

from datetime import datetime
from datetime import timedelta

from collections import deque
from dataclasses import dataclass
import itertools

# This class contains data for a line.
# We can have have multiple lines in a MsgPlot.
@dataclass
class LineInfo:
    msgClass: ...
    msgKey: str
    baseName: str
    fieldInfo: FieldInfo
    fieldSubindex: int
    dataArray: deque
    timeArray: deque
    curve: ...

start_time = datetime.now().timestamp()
def elapsedSeconds(timestamp):
    if timestamp > start_time:
        return timestamp - start_time
    return timestamp

# get a slice of the tail end of a deque
def deque_tail(d, count):
    start = max(0, len(d) - count)
    slice = list(itertools.islice(d, start, len(d)))
    return slice

# I added an optimization that replaces sequences of flat data
# with just two points, so we're starting to be a little smarter
# about storing data.  maybe we want to decimate very old data?
# that'll look wrong if user zooms in, though
# it also breaks time slider, because there's no longer the
# same number of points in each line for the same time period :(
# timeslider should likely change to using actual X axis ranges,
# and then we need to find points that falls in that time in the data?
# if time resets (which happens often when msgserver restarts or
# embedded processor resets depending on how time is managed,
# then time is non-linear and not necessarily always increasing in
# the arrays and any kind of smart search won't work well :(
class MsgPlot(QWidget):
    class PlotError(Exception):
        pass

    class NewPlotError(PlotError):
        pass

    Paused = QtCore.pyqtSignal(bool)
    AddLineError = QtCore.pyqtSignal(str)
    RegisterForMessage = QtCore.pyqtSignal(str)
    MAX_LENGTH = 1024
    def __init__(self, msgClass, msgKey, fieldName, runButton = None, clearButton = None, timeSlider = None, displayControls=True, fieldLabel=None):
        super(QWidget,self).__init__()
        
        newFieldName, fieldIndex = MsgPlot.split_fieldname(fieldName)
        fieldInfo = Messaging.findFieldInfo(msgClass.fields, newFieldName)
        if fieldInfo == None:
            raise MsgPlot.PlotError("Invalid field %s for message %s" % (newFieldName, msgClass.MsgName()))
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.pause = 0
        self.lineCount = 0
        self.showUnitsOnLegend = True
        self.units = fieldInfo.units
        self.lines = []

        yAxisLabel = fieldInfo.units
        xAxisLabel = "time (s)"
        self.plotWidget = pg.PlotWidget(labels={'left':yAxisLabel,'bottom':xAxisLabel})
        layout.addWidget(self.plotWidget)
        self.plotWidget.addLegend()
        self.addLine(msgClass, msgKey, fieldName, fieldLabel)

        # set up click handler to pause graph
        self.plotWidget.scene().sigMouseClicked.connect(self.mouseClicked)
        
        hLayout = QHBoxLayout()
        layout.addLayout(hLayout)
        
        # add a Pause/Run button
        if runButton == None:
            self.runButton = QPushButton("Pause")
        else:
            self.runButton = runButton
        self.runButton.clicked.connect(self.pauseOrRun)
        if displayControls:
            hLayout.addWidget(self.runButton)

        # add a 'Clear' button
        if clearButton == None:
            self.clearButton = QPushButton("Clear")
        else:
            self.clearButton = clearButton
        self.clearButton.clicked.connect(self.clearData)
        if displayControls:
            hLayout.addWidget(self.clearButton)

        # create slider bar to control time scale
        if timeSlider == None:
            self.timeSlider = QSlider(Qt.Horizontal)
            self.timeSlider.setMinimum(50)
            self.timeSlider.setMaximum(MsgPlot.MAX_LENGTH)
            self.timeSlider.setSingleStep(10)
            self.timeSlider.setPageStep(50)
        else:
            self.timeSlider = timeSlider
        self.timeSlider.valueChanged.connect(self.timeScaleChanged)
        if displayControls:
            hLayout.addWidget(QLabel("Time Scale"))
            hLayout.addWidget(self.timeSlider)
        
        self.plotWidget.dragEnterEvent = self.dragEnterEvent
        self.plotWidget.dragMoveEvent = self.dragMoveEvent
        self.plotWidget.dropEvent = self.dropEvent
        self.plotWidget.setAcceptDrops(1)

        # Create a timer to refresh after a small delay so that we can redraw
        # at a fixed rate instead of redrawing for each data point.
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(200)
        self.refresh_timer.timeout.connect(self.refresh)

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
            # add a line for whatever got dropped on us
            msgClass = type(item.msg)
            self.addLine(msgClass, item.msg_key, item.fieldName)
            # register to receive message updates for the new line
            self.RegisterForMessage.emit(item.msg_key)
        except MsgPlot.PlotError as e:
            self.AddLineError.emit(str(e))
    
    def clearData(self):
        for line in self.lines:
            line.dataArray.clear()
            line.timeArray.clear()
        self.refresh()

    def addLine(self, msgClass, msgKey, fieldName, fieldLabel = None):
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

        if self.showUnitsOnLegend:
            if fieldInfo.units != self.units:
                self.showUnitsOnLegend = True
                self.units = None
                #TODO how to edit existing left axis label?!?
                #print(str(self.plotWidget)) # how to print all attributes of an object?
                # pyqtgraph.widgets.PlotWidget.PlotWidget just shows up as <pyqtgraph.widgets.PlotWidget.PlotWidget object at 0x7f64c4644168>
                #self.plotWidget.labels['left'] = 'none?!?'
                for line in self.lines:
                    pass
                    #TODO how to edit existing legend
                    #line.curve.setName(line.baseName)

        if fieldIndex != None:
            self._addLine(msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel, self.showUnitsOnLegend)
        elif fieldInfo.count == 1:
            self._addLine(msgClass, msgKey, fieldInfo, 0, fieldLabel, self.showUnitsOnLegend)
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
                    self._addLine(msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel, self.showUnitsOnLegend)
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

    def _addLine(self, msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel = None, showUnits=False):
        lineName = fieldInfo.name
        baseName = lineName
        if showUnits and fieldInfo.units != '' and fieldInfo.units != 'UNKNOWN':
            lineName = lineName + " (%s)" % fieldInfo.units
        if fieldLabel != None:
            lineName = fieldLabel
            baseName = lineName
        try:
            if fieldInfo.count != 1:
                lineName += "["+str(fieldIndex)+"]"
        except:
            pass
        dataArray = deque([], maxlen=MsgPlot.MAX_LENGTH)
        timeArray = deque([], maxlen=MsgPlot.MAX_LENGTH)
        self.useHeaderTime = False
        # This is ugly, but try to make plotWidget.plot(pen) parameters that result in colors easy to distinguish.
        line_number = len(self.lines)
        line_count_estimate = 6
        while line_count_estimate < len(self.lines)+1:
            line_count_estimate = line_count_estimate + 6
            line_number = (line_number - 6)*2+1
        curve = self.plotWidget.plot(timeArray, dataArray, name=lineName, pen=(line_number,line_count_estimate))
        lineInfo = LineInfo(msgClass, msgKey, baseName, fieldInfo, fieldIndex, dataArray, timeArray, curve)
        self.lines.append(lineInfo)
        
    def pauseOrRun(self):
        self.pause = not self.pause
        self.runButton.setText("Run" if self.pause else "Pause")
        self.Paused.emit(self.pause)

    def mouseClicked(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.runButton.clicked.emit()
            #self.pauseOrRun()

    def addData(self, msg):
        # TODO what to do for things that can't be numerically expressed?  just ascii strings, i guess?
        for line in self.lines:
            try:
                if type(msg) != line.msgClass:
                    continue
                newDataPoint = Messaging.getFloat(msg, line.fieldInfo, line.fieldSubindex)
            except ValueError:
                print("ERROR! Plot of %s.%s cannot accept value %s" % (
                    self.msgClass.MsgName(),
                    line.fieldInfo.name,
                    str(Messaging.get(msg, line.fieldInfo, line.fieldSubindex))))
                continue
            try:
                timestamp = msg.hdr.GetTime()
                if Messaging.findFieldInfo(msg.hdr.fields, "Time").units == "ms":
                    timestamp = timestamp / 1000.0
                newTime = float(elapsedSeconds(timestamp))
                if newTime != 0:
                    self.useHeaderTime = True
                if not self.useHeaderTime:
                    newTime = elapsedSeconds(datetime.now().timestamp())
            except AttributeError:
                # if header has no time, fallback to PC time.
                newTime = elapsedSeconds(datetime.now().timestamp())
            
            # Disable this optimization because different lines having a different number of points
            # in the same period of time screws up X-axis autoscaling.
            if 0 and (len(line.dataArray) > 2 and
                # if the last two data points have the same value as us, then instead of adding a point,
                # we can just change the time of the previous point to our time
                line.dataArray[-2] == line.dataArray[-1] and
                line.dataArray[-1] == newDataPoint):
                line.timeArray[-1] = newTime
            else:
                # Add data in the fixed-size deque.
                # This will drop data off start when the deque is full,
                # such that plot appears to scroll horizontally so the last
                # point is always at the right edge.
                line.dataArray.append(newDataPoint)
                line.timeArray.append(newTime)

            # If the plot isn't paused, and the timer isn't running already, start it.
            if not self.pause and not self.refresh_timer.isActive():
                self.refresh_timer.start()

    def refresh(self):
        for line in self.lines:
            #line.curve.setData(line.timeArray, line.dataArray)
            timeArray = deque_tail(line.timeArray, self.timeSlider.value())
            dataArray = deque_tail(line.dataArray, self.timeSlider.value())
            line.curve.setData(timeArray, dataArray)

    def timeScaleChanged(self):
        self.refresh()

    @staticmethod
    def plotFactory(new_plot_callback, msgClass, fieldNames, msgKey = None, fieldLabels = None, runButton = None, clearButton = None, timeSlider = None, displayControls=True):
        msgPlot = None
        if len(fieldNames) == 0:
            fieldNames = [fieldInfo.name for fieldInfo in msgClass.fields]
        idx = 0
        for fieldName in fieldNames:
            fieldLabel = None
            if fieldLabels != None:
                fieldLabel = fieldLabels[idx]
            # if there's a plot widget, try adding a line to it
            if msgPlot != None:
                try:
                    msgPlot.addLine(msgClass, msgKey, fieldName, fieldLabel)
                except MsgPlot.NewPlotError as e:
                    # if error on adding to existing plot, then make a new plot
                    msgPlot = None
                except MsgPlot.PlotError as e:
                    print(str(e))
            
            # make new plot
            if msgPlot == None:
                try:
                    msgPlot = MsgPlot(msgClass, msgKey, fieldName, runButton, clearButton, timeSlider, displayControls, fieldLabel=fieldLabel)
                    msgPlot.msgClass = msgClass
                    new_plot_callback(msgPlot)
                except MsgPlot.PlotError as e:
                    print(str(e))
            idx += 1
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
        
        firstPlot = None
        for arg in argv[1:]:
            if not "=" in arg:
                continue
            argComponentList = arg.split("=")
            if argComponentList[0] == "--log":
                pass
            else:
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
                if firstPlot:
                    MsgPlot.plotFactory(self.newPlot, msgClass, fieldNames, **plotargs)
                else:
                    firstPlot = MsgPlot.plotFactory(self.newPlot, msgClass, fieldNames, displayControls=False)
                    plotargs = {"runButton":firstPlot.runButton, "clearButton":firstPlot.clearButton, "timeSlider":firstPlot.timeSlider, "displayControls":False}
        # add plot controls
        hLayout = QHBoxLayout()
        self.plotlayout.addLayout(hLayout)
        hLayout.addWidget(firstPlot.runButton)
        hLayout.addWidget(firstPlot.clearButton)
        hLayout.addWidget(QLabel("Time Scale"))
        hLayout.addWidget(firstPlot.timeSlider)


    def newPlot(self, plot):
        self.plotlayout.addWidget(QLabel(plot.msgClass.MsgName()))
        self.plotlayout.addWidget(plot)
        if not plot.msgClass.ID in self.msgPlots:
            self.msgPlots[plot.msgClass.ID] = []
        self.msgPlots[plot.msgClass.ID].append(plot)
    
    def ProcessMessage(self, msg):
        if msg.ID in self.msgPlots:
            self.logMsg(msg)
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
