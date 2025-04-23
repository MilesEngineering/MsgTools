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
    evaluator: ...

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

import ast
import operator

# This class is to evaluate arithmetical expressions that contain variable
# names for a specific value of those variables.
class EquationEvaluator:
    OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                 ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
                 ast.USub: operator.neg}
    def __init__(self, equation):
        if "[" in equation or "]" in equation:
            raise KeyError("equation %s has brackets, which are not supported!" % (equation))
            self.variable_name = None
            return
        self.top_node = ast.parse(equation, mode='eval')
        self.variable_name = EquationEvaluator.find_variable_name(self.top_node)
        if self.variable_name:
            self.equation = equation.replace(" ","")
    
    def has_equation(self):
        return self.variable_name != self.equation

    def evaluate(self, variable_value):
        self.variable_value = variable_value
        return self.node_eval(self.top_node.body)

    def node_eval(self, node):
        if isinstance(node, ast.Name):
            if node.id == self.variable_name:
                return self.variable_value
            raise KeyError(node.id)
        elif isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return EquationEvaluator.OPERATORS[type(node.op)](self.node_eval(node.left), self.node_eval(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return EquationEvaluator.OPERATORS[type(node.op)](self.node_eval(node.operand))
        else:
            raise TypeError(node)

    @staticmethod
    def find_variable_name(node):
        if isinstance(node, ast.Name):
            return node.id
        for child in ast.iter_child_nodes(node):
            name = EquationEvaluator.find_variable_name(child)
            if name:
                return name
        return None

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
    MAX_LENGTH = 4096
    MAX_TIME = 60*5
    def __init__(self, msgClass, msgKey, fieldName, runButton = None, clearButton = None, timeSlider = None, displayControls=True, fieldLabel=None, multiple_messages=False):
        super(QWidget,self).__init__()
        
        newFieldName, fieldIndex, evaluator = MsgPlot.split_fieldname(fieldName)
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
        self.addLine(msgClass, msgKey, fieldName, fieldLabel, multiple_messages)

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
            self.timeSlider.setMinimum(1)
            self.timeSlider.setMaximum(MsgPlot.MAX_TIME)
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
        fieldEvaluator = None
        # Look for brackets, and use them to find an array index.
        # Don't do an equation evaluator if there are brackets, it won't work
        # properly because AST will try to do array indexing, and we don't
        # want it to.
        if '[' in fieldName  and ']' in fieldName:
            splits = fieldName.split('[')
            splits[1] = splits[1].replace(']','')
            fieldName = splits[0]
            fieldIndex = int(splits[1])
        else:
            try:
                evaluator = EquationEvaluator(fieldName)
                if evaluator.has_equation():
                    fieldName = evaluator.variable_name
                    fieldEvaluator = evaluator
            except SyntaxError as e:
                print("MsgPlot.split_fieldname(%s): exception [%s], ignoring EquationEvaluator" % (fieldName, e))
        return (fieldName, fieldIndex, fieldEvaluator)

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

    def addLine(self, msgClass, msgKey, fieldName, fieldLabel = None, multiple_messages=False):
        fieldName, fieldIndex, evaluator = MsgPlot.split_fieldname(fieldName)
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
            self._addLine(msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel, self.showUnitsOnLegend, evaluator, multiple_messages)
        elif fieldInfo.count == 1:
            self._addLine(msgClass, msgKey, fieldInfo, 0, fieldLabel, self.showUnitsOnLegend, evaluator, multiple_messages)
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
                    self._addLine(msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel, self.showUnitsOnLegend, evaluator, multiple_messages)
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

    def _addLine(self, msgClass, msgKey, fieldInfo, fieldIndex, fieldLabel = None, showUnits=False, evaluator=None, multiple_messages=False):
        lineName = fieldInfo.name
        baseName = lineName
        if evaluator:
            lineName = evaluator.equation
        if multiple_messages:
            lineName = msgClass.MsgName() + "." + lineName
        try:
            if fieldInfo.count != 1:
                lineName += "["+str(fieldIndex)+"]"
        except:
            pass
        if showUnits and fieldInfo.units != '' and fieldInfo.units != 'UNKNOWN':
            lineName = lineName + " (%s)" % fieldInfo.units
        if fieldLabel != None:
            lineName = fieldLabel
            baseName = lineName
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
        lineInfo = LineInfo(msgClass, msgKey, baseName, fieldInfo, fieldIndex, dataArray, timeArray, curve, evaluator)
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
                if line.evaluator != None:
                    newDataPoint = line.evaluator.evaluate(newDataPoint)
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
            
            if (len(line.dataArray) > 2 and
                line.dataArray[-2] == line.dataArray[-1] and
                line.dataArray[-1] == newDataPoint):
                # if the last two data points have the same value as us, then instead of adding a point,
                # we can just change the time of the previous point to our time
                line.timeArray[-1] = newTime
            else:
                # Add data in the fixed-size deque.
                # This will drop data off start when the deque is full.
                line.dataArray.append(newDataPoint)
                line.timeArray.append(newTime)

            # If the plot isn't paused, and the timer isn't running already, start it.
            if not self.pause and not self.refresh_timer.isActive():
                self.refresh_timer.start()

    def refresh(self):
        # Read the time scale value from the slider
        time_scale = self.timeSlider.value()
        # look for the time of the newest data on any line on this plot
        max_time = -1
        for line in self.lines:
            if len(line.timeArray) > 0:
                max_time = max(max_time, line.timeArray[-1])
        # if there was no data, then try to leave the max time at whatever was visible
        if max_time == -1:
            old_xrange = self.plotWidget.viewRange()[0]
            max_time = int(old_xrange[1])

        # set the minimum time to be less than max time by the scale
        min_time = max_time - time_scale
        self.plotWidget.setRange(xRange=[min_time, max_time])
        point_count = MsgPlot.MAX_LENGTH

        # Set the line data to the time and data arrays
        for line in self.lines:
            line.curve.setData(line.timeArray, line.dataArray)

    def timeScaleChanged(self):
        self.refresh()

    def setYAxis(self, yaxis):
        self.plotWidget.setRange(yRange=[yaxis[0], yaxis[1]])

    @staticmethod
    def plotFactory(new_plot_callback, msgClass, fieldNames, msgKey = None, fieldLabels = None, runButton = None, clearButton = None, timeSlider = None, displayControls=True, multiple_messages=False):
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
                    msgPlot.addLine(msgClass, msgKey, fieldName, fieldLabel, multiple_messages)
                except MsgPlot.NewPlotError as e:
                    # if error on adding to existing plot, then make a new plot
                    msgPlot = None
                except MsgPlot.PlotError as e:
                    print(str(e))
            
            # make new plot
            if msgPlot == None:
                try:
                    msgPlot = MsgPlot(msgClass, msgKey, fieldName, runButton, clearButton, timeSlider, displayControls, fieldLabel=fieldLabel, multiple_messages=multiple_messages)
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
