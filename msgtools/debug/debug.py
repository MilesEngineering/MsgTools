#!/usr/bin/env python3
import argparse
import collections
import json
import os
import re
import struct
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets

from .findprints import format_specifier_list

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging
import msgtools.lib.gui
import msgtools.lib.createmsgdialog
import msgtools.lib.msgjson as msgjson
import msgtools.debug.launcher as launcher

DESCRIPTION='''DebugPrint provides a graphical interface that allows you to view debug messages, and send
    binary messages and text commands.  It tries to be pretty flexible about what messages are used, by
    looking up messages by MessageAlias, and by accepting Thread/Stream as synonyms.'''

QUERY_DEVICE_INFO_TIMEOUT = 3.0
QUERY_STREAM_INFO_TIMEOUT = 5.0

DebugInfo = collections.namedtuple('DebugInfo', ['formatStr', 'filename', 'linenumber'])

def float_from_integer(integer):
    return struct.unpack('!f', struct.pack('!I', integer))[0]

class DebugStream(QtWidgets.QWidget):
    messageOutput = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)
    def __init__(self, streamID, debugDevice, debugWidget):
        super(DebugStream, self).__init__()
        self.debugDevice = debugDevice
        self.debugWidget = debugWidget
        self.name = "Stream" + str(streamID)
        self.widget = msgtools.lib.gui.TreeWidget()
        self.widget.debugStream = self
        self.streamID = streamID
        self.widget.priority = 1000
        self.widget.itemDoubleClicked.connect(self.debugWidget.tableDataDoubleClicked)

        if self.debugWidget.setThresholdMsg:
            self.m_tabMenu = QtWidgets.QMenu()
            self.m_tabMenu.addSection("Device " + self.debugDevice.route + ", Stream " + str(streamID))
            if self.debugWidget.getDeviceInfoMsg:
                queryAction = self.m_tabMenu.addAction("Query Device")
                queryAction.triggered.connect(self.debugDevice.getDeviceInfo)
            if self.debugWidget.getStreamInfoMsg:
                queryAction = self.m_tabMenu.addAction("Query Stream")
                queryAction.triggered.connect(self.getStreamInfo)
            self.m_tabMenu.addSection("")
            actionGroup = QtWidgets.QActionGroup(self)
            for debugLevel in self.debugWidget.setThresholdMsg.Priorities.keys():
                debugThresholdChangedAction = self.m_tabMenu.addAction(debugLevel)
                debugThresholdChangedAction.setCheckable(1)
                actionGroup.addAction(debugThresholdChangedAction)
                debugThresholdChangedAction.triggered.connect(self.debugThresholdChanged)

        # add it to the tab widget, so the user can see it
        added = 0
        tabName = debugDevice.name+", " + self.name
        for index in range(0,self.debugWidget.tabWidget.count()):
            if(tabName < self.debugWidget.tabWidget.tabText(index)):
                self.debugWidget.tabWidget.insertTab(index, self.widget, tabName)
                added = 1
                break
        if not added:
            self.debugWidget.tabWidget.addTab(self.widget, tabName)

        # add table header, one column for each message field
        tableHeader = []
        tableHeader.append("Time (ms)")
        tableHeader.append("Priority")
        tableHeader.append("File")
        tableHeader.append("Line")
        tableHeader.append("Message")
        
        self.widget.setHeaderLabels(tableHeader)

        # daisy-chain our signals to the debugDevice's signals
        self.messageOutput.connect(self.debugDevice.messageOutput)
        self.statusUpdate.connect(self.debugDevice.statusUpdate)

    def clear(self):
        self.widget.clear()

    def Rename(self, deviceName, streamName=None):
        if streamName == None:
            # if we're renaming because we just learned the deviceName, we ought to query the stream name.
            self.getStreamInfo()
        else:
            # if we got the stream name, then set it.
            self.name = streamName
        newName = deviceName + ", " + self.name
        tabIndex = self.debugWidget.tabWidget.indexOf(self.widget)
        if tabIndex < 0:
            self.statusUpdate.emit("Warning!  Couldn't find debug tab for device " + route + " stream " + str(streamID))
        else:
            self.debugWidget.tabWidget.setTabText(tabIndex, newName)

    def debugThresholdChanged(self):
        action = self.sender()
        msg = self.debugWidget.setThresholdMsg()
        Messaging.SetMsgRoute(msg, self.debugDevice.route.split("/"))
        msg.SetStreamID(self.streamID)
        msg.SetDebugThreshold(action.text())
        self.messageOutput.emit(msg)

    def getStreamInfo(self):
        msg = self.debugWidget.getStreamInfoMsg()
        Messaging.SetMsgRoute(msg, self.debugDevice.route.split("/"))
        try:
            msg.SetStreamID(self.streamID)
        except AttributeError:
            msg.SetThreadID(self.streamID)
        self.messageOutput.emit(msg)

    def AddPrintMessage(self, msg, firstTime):
        msgStringList = []
        try:
            msgStringList.append(str(msg.hdr.GetTime()))
        except AttributeError:
            msgStringList.append("Unknown")
        text = ""
        filename = ""
        linenumber = ""
        try:
            priority = msg.GetPriority()
            priorityInt = msg.GetPriority(1)
            priorityIntError = msg.Priorities["Error"]
        except AttributeError:
            priority = ""
            priorityInt = 0
            priorityIntError = 255
        if type(msg) == self.debugWidget.printfMsg:
            text = msg.GetBuffer()
            matchObj = re.search( r'(.*), (\d+): (.*)', text)
            if matchObj != None:
                filename = matchObj.group(1).strip()
                linenumber = matchObj.group(2).strip()
                text = matchObj.group(3).strip()
        elif type(msg) == self.debugWidget.printfIDMsg:
            # need to look up the format string in the dictionary, and use it to print a string to display!
            formatStringId = msg.GetFormatStringID()
            strFormatError = 0
            if formatStringId < len(self.debugDevice.dictionary):
                info = self.debugDevice.dictionary[formatStringId]
                filename = info.filename
                linenumber = info.linenumber
                # need to evaluate the formatStr and parameters to produce a new string!
                try:
                    format_specifiers = format_specifier_list(info.formatStr)
                    paramsNeeded = min(info.formatStr.count("%"), msg.GetParameters.count)
                    params = []
                    for i in range(0, paramsNeeded):
                        try:
                            if 'f' in format_specifiers[i]:
                                value = float_from_integer(msg.GetParameters(i))
                            else:
                                value = int(msg.GetParameters(i))
                        except IndexError:
                            print("i is %d, len(format_specifiers) is %d" % (i, len(format_specifiers)))
                            print(format_specifiers)
                        except struct.error:
                            value = 0
                        params.append(value)
                    text = info.formatStr % tuple(params)
                except TypeError:
                    strFormatError = 1
            else:
                strFormatError = 1

            # if we couldn't format the string for whatever reason, fall back to just displaying the parameters
            if strFormatError:
                text = "undecoded %d(" % (formatStringId)
                for i in range(0,4):
                    try:
                        text += str(msg.GetParameters(i))+","
                    except struct.error:
                        pass
                if text.endswith(","):
                    text = text[:-1]
                text += ")"
                # if there's a message to query device info, and we haven't done that lately, do it again
                if self.debugWidget.getDeviceInfoMsg and time.time() > self.debugDevice._lastDeviceInfoQueryTime + QUERY_DEVICE_INFO_TIMEOUT:
                    self.debugDevice.getDeviceInfo()
                    
        msgStringList.append(str(priority))
        msgStringList.append(filename)
        msgStringList.append(str(linenumber))
        msgStringList.append(text)

        msgItem = QtWidgets.QTreeWidgetItem(None,msgStringList)
        color = 0
        if(priority == "Error" or priorityInt > priorityIntError):
            color = QtCore.Qt.red
        elif(priority == "Warning"):
            color = QtGui.QColor("darkOrange")
        elif(priority != "Info"):
            color = QtCore.Qt.blue
        if color != 0:
            font = msgItem.font(0)
            brush = msgItem.foreground(0)
            font.setBold(1)
            brush.setColor(color)
            for column in range(0,5):
                msgItem.setFont(column, font)
                msgItem.setForeground(column, brush)
                msgItem.setBackground(column, brush)
        # if new priority is more severe than old priority, change color
        oldPriority = self.widget.priority
        if priorityInt < oldPriority:
            index = self.debugWidget.tabWidget.indexOf(self.widget)
            if color == 0:
                color = QtCore.Qt.darkGreen
            self.debugWidget.tabWidget.tabBar().setTabTextColor(index, color)
            self.widget.priority = priorityInt
        
        self.widget.addTopLevelItem(msgItem)
        if(self.debugWidget.autoscroll):
            self.widget.scrollToItem(msgItem)
        # we should have an option to log PrintfID messages as text, or else we should
        # send them out as Printf messages (as long as they don't go to the device!),
        # so standard logs will show them in an easy to read form

        if firstTime:
            for col in range(0, 5):
                self.widget.resizeColumnToContents(col)

class DebugDevice(QtWidgets.QWidget):
    messageOutput = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)
    def __init__(self, debugWidget, route, dictionaryFilename):
        super(DebugDevice, self).__init__()
        self.debugWidget = debugWidget
        self.route = route
        self.name = "Dev"+route
        self.dictionary = []
        self.dictionaryID = None
        self.dictionaryFilename = None
        if dictionaryFilename:
            self.ReadDictionary(dictionaryFilename)

        self.streams = {}
        self._lastDeviceInfoQueryTime = 0
        
        # daisy-chain our signals to the debugWidget's signals
        self.messageOutput.connect(self.debugWidget.messageOutput)
        self.statusUpdate.connect(self.debugWidget.statusUpdate)

    def clear(self):
        for streamID, stream in self.streams.items():
            stream.clear()

    def getDeviceInfo(self):
        msg = self.debugWidget.getDeviceInfoMsg()
        Messaging.SetMsgRoute(msg, self.route.split("/"))
        self.messageOutput.emit(msg)
        self._lastDeviceInfoQueryTime = time.time()

    def ReadDictionary(self, filename):
        self.dictionaryFilename = filename
        self.dictionary = []
        nextId = 0
        try:
            with open(filename, 'r') as formatStringFile:
                lines = formatStringFile.read().splitlines()
                for line in lines:
                    matchObj = re.search( r'(\d+).*:\s*"([^"]*)", (.*), (\d+)', line)
                    if line.startswith("#"):
                        matchObj = re.search( r'Dictionary md5 is (.*)', line)
                        if matchObj != None:
                            self.dictionaryID = matchObj.group(1).strip()
                            self.statusUpdate.emit("Device %s read dictionary %s" % (self.route, self.dictionaryID))
                    else:
                        data_dict = json.loads(line)
                        id = data_dict["id"]
                        if int(id) != nextId:
                            self.statusUpdate.emit("ERROR! Format string ID " + str(id) + " != " + str(nextId))
                        info = DebugInfo(data_dict["format"], data_dict["filename"], data_dict["linenumber"])
                        self.dictionary.append(info)
                        nextId += 1
        except FileNotFoundError:
            self.statusUpdate.emit("Cannot open file %s" % filename)

    def ProcessMessage(self, msg):
        if type(msg) == self.debugWidget.deviceInfoMsg:
            dictionaryID = ""
            for i in range(msg.GetDebugStringDictionaryID.count):
                dictionaryID += '{:02x}'.format(msg.GetDebugStringDictionaryID(i))
            if dictionaryID != self.dictionaryID:
                if "00000000000000000000000000000000" in dictionaryID:
                    self.statusUpdate.emit("ERROR!  Dictionary ID %s invalid, being ignored" % self.statusUpdate.emit)
                else:
                    # If dictionary ID changed or wasn't previously set, load the dictionary.
                    self.ReadDictionary("%s/PrintfDictionaries/%s.json" % (Messaging.objdir, dictionaryID))

            try:
                deviceName = msg.GetDeviceName()
            except AttributeError:
                deviceName = msg.GetName()
            self.name = deviceName
            for streamID,stream in self.streams.items():
                stream.Rename(deviceName)
            return

        if type(msg) == self.debugWidget.streamInfoMsg:
            try:
                streamID = msg.GetStreamID()
            except AttributeError:
                streamID = msg.GetThreadID()
            try:
                streamName = msg.GetStreamName()
            except AttributeError:
                try:
                    streamName = msg.GetThreadName()
                except AttributeError:
                    streamName = msg.GetName()
            if not streamID in self.streams:
                self.streams[streamID] = DebugStream(streamID, self, self.debugWidget)

            self.streams[streamID].Rename(self.name, streamName)
            return

        # only handle Printf and PrintfID messages!
        try:
            if type(msg) != self.debugWidget.printfMsg and type(msg) != self.debugWidget.printfIDMsg:
                return
        except NameError:
            return
        
        try:
            streamID = msg.GetStreamID()
        except AttributeError:
            try:
                streamID = msg.GetThreadID()
            except AttributeError:
                streamID = 0
        
        if streamID in self.streams:
            firstTime = 0
        else:
            firstTime = 1
            self.streams[streamID] = DebugStream(streamID, self, self.debugWidget)

        self.streams[streamID].AddPrintMessage(msg, firstTime)

# this is a widget used for debug purposes.
# it incorporates:
# 1) entry text box
#   a. to send binary messages
#   b. to send text commands
# 2) cmd/response text display to show:
#   a. entered commands
#   b. responses
# 3) separate tabs for debug text output
# 4) controls to set threshold for debug output per stream of each device
class MsgDebugWidget(QtWidgets.QWidget):
    messageOutput = QtCore.pyqtSignal(object)
    autocompleted   = QtCore.pyqtSignal(str)
    statusUpdate = QtCore.pyqtSignal(str)
    def __init__(self, debugdicts, parent=None):
        super(MsgDebugWidget, self).__init__()
        
        # find classes for print messages.
        try:
            self.printfMsg = Messaging.Messages.DebugPrintf
        except AttributeError:
            self.printf = None
        try:
            self.printfIDMsg = Messaging.Messages.DebugPrintfID
        except AttributeError:
            self.printfIDMsg = None
        try:
            self.getDeviceInfoMsg = Messaging.Messages.GetDeviceDebugInfo
        except AttributeError:
            self.getDeviceInfoMsg = None
        try:
            self.getStreamInfoMsg = Messaging.Messages.GetStreamDebugInfo
        except AttributeError:
            self.getStreamInfoMsg = None
        try:
            self.setThresholdMsg = Messaging.Messages.SetDebugThreshold
        except AttributeError:
            self.setThresholdMsg = None
        try:
            self.deviceInfoMsg = Messaging.Messages.DebugDeviceInfo
        except AttributeError:
            self.deviceInfoMsg = None
        try:
            self.streamInfoMsg = Messaging.Messages.DebugStreamInfo
        except AttributeError:
            self.streamInfoMsg = None
        
        # tab widget to show multiple stream of print statements, one per tab
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.tabBar().tabBarClicked.connect(self.createTabContextMenu)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tabWidget)
        self.setLayout(vbox)
        
        # tab for text commands
        self.textEntryWidget = msgtools.lib.gui.MsgCommandWidget(self)
        self.tabWidget.addTab(self.textEntryWidget, "Cmd/Reply")
        self.textEntryWidget.commandEntered.connect(self.newCommandEntered)
        self.textEntryWidget.messageEntered.connect(self.newMessageEntered)
        self.textEntryWidget.autocompleted.connect(self.autocompleted)
        
        # tracking what reply to expect
        self.expectedReply = None
        
        self.fileWatcher = QtCore.QFileSystemWatcher()

        # hash table of devices by route
        self.devices = {}
        
        for d in debugdicts:
            route, dictName = d.split("=")
            self.devices[route] = DebugDevice(self, route, dictName)
            self.fileWatcher.addPath(dictName)

        # whether we should autoscroll as data is added
        self.autoscroll = 1
        self.scrollAction = QtWidgets.QAction('&Scroll', self)
        self.scrollAction.setCheckable(1)
        self.scrollAction.setChecked(self.autoscroll)
        self.scrollAction.triggered.connect(self.switchScroll)

        self.fileWatcher.fileChanged.connect(self.fileChanged)

    def clearTab(self):
        self.tabWidget.currentWidget().clear()
    
    def clearAllTabs(self):
        for route, device in self.devices.items():
            device.clear()
        
    def switchScroll(self):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def tableDataDoubleClicked(self, treeWidgetItem, column):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def createTabContextMenu(self, tabIndex):
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.RightButton:
            return
        try:
            self.tabWidget.currentWidget().debugStream
        except AttributeError:
            return
        self.tabWidget.currentWidget().debugStream.m_tabMenu.popup(QtGui.QCursor.pos())

    def newCommandEntered(self, cmd):
        try:
            tc = Messaging.Messages.MsgText.Command()
            tc.SetBuffer(cmd)
            tc.hdr.SetDataLength(len(cmd)+1)
            self.messageOutput.emit(tc)
        except:
            self.textEntryWidget.addText("\nWARNING: No message named/aliased to MsgText.Command exists, not sending text\n> ")
    
    def newMessageEntered(self, msg):
        self.expectedReply = msg.MsgName().rsplit(".",1)[0]
        self.messageOutput.emit(msg)

    def ReadDictionary(self, route, filename):
        nextId = 0
        if route in self.devices:
            self.devices[route].ReadDictionary(filename)
        else:
            self.devices[route] = DebugDevice(self, route, filename)
    
    def ProcessMessage(self, msg):
        # Create the DebugDevice if it doesn't already exist
        route = "/".join(Messaging.MsgRoute(msg))
        if not route in self.devices:
            self.devices[route] = DebugDevice(self, route, None)

        # handle text replies
        alreadyPrintedText = False
        try:
            if type(msg) == Messaging.Messages.MsgText.Response:
                text = msg.GetBuffer()
                text = text.replace("\\n","\n")
                text = text.replace("\\r","")
                self.textEntryWidget.addText(text)
                if "error" in text.lower():
                    color = QtCore.Qt.red
                elif "warning" in text.lower():
                    color = QtGui.QColor("darkOrange")
                else:
                    color = QtGui.QColor("darkGreen")
                self.tabWidget.tabBar().setTabTextColor(0, color)
                alreadyPrintedText = True
        except:
            pass
        
        if not alreadyPrintedText and self.expectedReply and msg.MsgName().startswith(self.expectedReply):
            outputString = msgjson.toJson(msg)
            self.tabWidget.tabBar().setTabTextColor(0, QtGui.QColor("darkGreen"))
            self.textEntryWidget.addText(outputString+"\n> ")

        self.devices[route].ProcessMessage(msg)

    def tabChanged(self, index):
        # when user selects a tab, change it's color back to black
        w = self.tabWidget.widget(index)
        w.priority = 1000
        self.tabWidget.tabBar().setTabTextColor(index, QtCore.Qt.black)

    def fileChanged(self, path):
        for route, device in self.devices.items():
            if device.dictionaryFilename == path:
                device.ReadDictionary(device.dictionaryFilename)
                self.statusUpdate.emit("updating device %s dictionary %s" % (route, device.dictionaryFilename))
                QtCore.QTimer.singleShot(3000, self.clearStatus)
                return
        self.statusUpdate.emit("Device %s dictionary %s not found" % (route, device.dictionaryFilename))
    def clearStatus(self):
        self.statusUpdate.emit("")

class DebugPrint(msgtools.lib.gui.Gui):
    def __init__(self, args, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Debug Print 0.1", args, parent)
        self.setWindowIcon(QtGui.QIcon(launcher.info().icon_filename))

        if args.debugdicts:
            debugdictList = args.debugdicts.split(",")
        else:
            debugdictList = []
        self.debugWidget = MsgDebugWidget(debugdictList)
        self.debugWidget.statusUpdate.connect(self.statusUpdate)
        self.setCentralWidget(self.debugWidget)
        self.debugWidget.messageOutput.connect(self.SendMsg)
        
        # menu items to change view
        clearAction = QtWidgets.QAction('&Clear', self)
        clearAllAction = QtWidgets.QAction('Clear &All', self)

        menubar = self.menuBar()
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(clearAction)
        viewMenu.addAction(clearAllAction)
        viewMenu.addAction(self.debugWidget.scrollAction)

        clearAction.triggered.connect(self.debugWidget.clearTab)
        clearAllAction.triggered.connect(self.debugWidget.clearAllTabs)

        # menu items to control the device output
        if self.debugWidget.getDeviceInfoMsg or self.debugWidget.setThresholdMsg:
            controlMenu = menubar.addMenu('&Control')

        if self.debugWidget.getDeviceInfoMsg:
            queryDeviceAction = QtWidgets.QAction('&Query Devices', self)
            queryDeviceAction.triggered.connect(self.QueryDeviceDebugInfo)
            controlMenu.addAction(queryDeviceAction)
        
        if self.debugWidget.getStreamInfoMsg:
            queryStreamAction = QtWidgets.QAction('&Query Streams', self)
            queryStreamAction.triggered.connect(self.QueryStreamDebugInfo)
            controlMenu.addAction(queryStreamAction)

        if self.debugWidget.setThresholdMsg:
            setThresholdAction = QtWidgets.QAction('&Set Threshold', self)
            setThresholdAction.triggered.connect(self.SetThresholdDialog)
            controlMenu.addAction(setThresholdAction)

        # event-based way of getting messages
        self.RxMsg.connect(self.debugWidget.ProcessMessage)

    def QueryDeviceDebugInfo(self):
        # for each device we've seen any message from, query the dictionary
        for route, device in self.debugWidget.devices.items():
            # should we re-query devices we already have a dictionary ID for?
            if 1: #device.dictionaryID == None:
                device.getDeviceInfo()

    def QueryStreamDebugInfo(self):
        # for each stream of each device we've seen any message from, query
        for route, device in self.debugWidget.devices.items():
            for streamID, stream in device.streams.items():
                # should we re-query streams we already have a name for?
                if 1: #stream.name == None:
                    stream.getStreamInfo()

    def SetThresholdDialog(self):
        # open a dialog to let use set debug output threshold
        # for a specified device and stream
        dlg = msgtools.lib.createmsgdialog.CreateMsgDialog(self, self.debugWidget.setThresholdMsg)
        if dlg.exec_():
            self.SendMsg(dlg.msg)

def main():
    # Setup a command line processor...
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
    parser.add_argument('--debugdicts', help=''''Dictionaries to use to lookup debug message format strings, of the form 0=pathToDictionary0,1=pathToDictionary1.''')
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    msgApp = DebugPrint(args)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
