#!/usr/bin/env python3
import re
import collections
import sys
import struct
import argparse

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../../MsgTools")
    sys.path.append(srcroot)
    try:
        from msgtools.lib.messaging import Messaging
    except ImportError:
        print("ERROR!  You must have MsgTools in a place that can be found!")
        print("If you don't have it installed via pip, clone it from git and do 'make develop' in MsgTools")
        sys.exit(1)

import msgtools.lib.gui
import msgtools.lib.msgjson as msgjson

DESCRIPTION='''DebugPrint provides a graphical interface that allows you to view debug messages, and send
    binary messages and text commands.'''

# this is a widget used for debug purposes.
# it incorporates:
# 1) entry text box
#   a. to send binary messages
#   b. to send text commands
# 2) cmd/response text display to show:
#   a. entered commands
#   b. responses
# 3) separate tabs for debug text output
class MsgDebugWidget(QtWidgets.QWidget):
    messageOutput = QtCore.pyqtSignal(object)
    def __init__(self, argv=[], parent=None):
        super(MsgDebugWidget, self).__init__()
        
        # find classes for print messages
        global printf
        global printfID
        try:
            printf = Messaging.Messages.DebugPrintf
        except AttributeError:
            printf = None
        try:
            printfID = Messaging.Messages.DebugPrintfID
        except AttributeError:
            printfID = None
        
        # tab widget to show multiple stream of print statements, one per tab
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.tabChanged)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tabWidget)
        self.setLayout(vbox)
        
        # tab for text commands
        self.textEntryWidget = msgtools.lib.gui.MsgCommandWidget(self)
        self.tabWidget.addTab(self.textEntryWidget, "Cmd/Reply")
        self.textEntryWidget.commandEntered.connect(self.newCommandEntered)
        self.textEntryWidget.messageEntered.connect(self.newMessageEntered)
        
        # tracking what reply to expect
        self.expectedReply = None
        
        # list of hash table to lookup the widget for a stream, by stream ID
        self.msgWidgets = []
        
        self.fileWatcher = QtCore.QFileSystemWatcher()
        # array of format string info
        self.dictionaries = []
        self.formatStringFilenames = []
        for dictName in argv[1:]:
            # ignore arguments that start with - or --, they are command-line options, not dictionary names!
            if not dictName.startswith('-'):
                self.formatStringFilenames.append(dictName)
        for deviceID in range(0, len(self.formatStringFilenames)):
            print("reading dictionary["+str(deviceID)+"] " + self.formatStringFilenames[deviceID])
            self.ReadDictionary(deviceID, self.formatStringFilenames[deviceID])
            self.fileWatcher.addPath(self.formatStringFilenames[deviceID])

        # whether we should autoscroll as data is added
        self.autoscroll = 1

        self.fileWatcher.fileChanged.connect(self.fileChanged)

    def clearTab(self):
        self.tabWidget.currentWidget().clear()
    
    def clearAllTabs(self):
        for device in self.msgWidgets:
            for stream, widget in device.items():
                widget.clear()
        
    def switchScroll(self):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def tableDataDoubleClicked(self, treeWidgetItem, column):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

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

    def ReadDictionary(self, deviceID, filename):
        nextId = 0
        if deviceID >= len(self.dictionaries):
            self.dictionaries.append([])
            self.msgWidgets.append({})
        else:
            self.dictionaries[deviceID] = []
        with open(filename, 'r') as formatStringFile:
            lines = formatStringFile.read().splitlines()
            for line in lines:
                matchObj = re.search( r'(\d+).*:\s*"([^"]*)", (.*), (\d+)', line)
                if matchObj != None:
                    DebugInfo = collections.namedtuple('DebugInfo', ['formatStr', 'filename', 'linenumber'])
                    id = matchObj.group(1).strip()
                    if int(id) != nextId:
                        print("ERROR! Format string ID " + str(id) + " != " + str(nextId))
                    formatStr = matchObj.group(2).strip()
                    filename = matchObj.group(3).strip()
                    linenumber = matchObj.group(4).strip()
                    info = DebugInfo(formatStr, filename, linenumber)
                    self.dictionaries[deviceID].append(info)
                    nextId += 1
    
    def ProcessMessage(self, msg):
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

        # only handle Printf and PrintfID messages!
        try:
            if type(msg) != printf and type(msg) != printfID:
                return
        except NameError:
            return
        
        try:
            deviceID = msg.hdr.GetDeviceID()
        except AttributeError:
            deviceID = 0
        if type(msg) == printfID:
            # make sure we have a dictionary for the device ID
            if deviceID >= len(self.dictionaries):
                print("ERROR!  deviceID " + str(deviceID) + " is invalid!")
                #return

        try:
            streamID = msg.GetStreamID()
        except AttributeError:
            streamID = 0
        
        # create a new Tree widget to display the print info
        firstTime = 0
        while deviceID >= len(self.msgWidgets):
            self.msgWidgets.append({})

        if not(streamID in self.msgWidgets[deviceID]):
            firstTime = 1
            self.AddNewTab(deviceID, streamID)
        
        self.AddPrintMessage(deviceID, streamID, msg)
        if firstTime:
            for col in range(0, 5):
                self.msgWidgets[deviceID][streamID].resizeColumnToContents(col)

    def AddNewTab(self, deviceID, streamID):
        msgWidget = msgtools.lib.gui.TreeWidget()
        msgWidget.streamID = streamID
        msgWidget.priority = 1000
        msgWidget.itemDoubleClicked.connect(self.tableDataDoubleClicked)
        header = msgWidget.header()
        header.myTreeWidget = msgWidget
        
        # add it to the tab widget, so the user can see it
        added = 0
        tabName = "Stream " + str(streamID)
        # only add device number to the tab if we have more than one device
        if len(self.dictionaries) > 1:
            tabName = "Dev"+str(deviceID)+", " + tabName
        for index in range(0,self.tabWidget.count()):
            if(tabName < self.tabWidget.tabText(index)):
                self.tabWidget.insertTab(index, msgWidget, tabName)
                added = 1
                break
        if not added:
            self.tabWidget.addTab(msgWidget, tabName)

        # add table header, one column for each message field
        tableHeader = []
        tableHeader.append("Time (ms)")
        tableHeader.append("Priority")
        tableHeader.append("File")
        tableHeader.append("Line")
        tableHeader.append("Message")
        
        msgWidget.setHeaderLabels(tableHeader)
        
        # store a pointer to it, so we can find it next time (instead of creating it again)
        self.msgWidgets[deviceID][streamID] = msgWidget

    def AddPrintMessage(self, deviceID, streamID, msg):
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
        except AttributeError:
            priority = ""
            priorityInt = 0
        if type(msg) == printf:
            text = msg.GetBuffer()
            matchObj = re.search( r'(.*), (\d+): (.*)', text)
            if matchObj != None:
                filename = matchObj.group(1).strip()
                linenumber = matchObj.group(2).strip()
                text = matchObj.group(3).strip()
        elif type(msg) == printfID:
            # need to look up the format string in the dictionary, and use it to print a string to display!
            formatStringId = msg.GetFormatStringID()
            strFormatError = 0
            if deviceID < len(self.dictionaries) and formatStringId < len(self.dictionaries[deviceID]):
                info = self.dictionaries[deviceID][formatStringId]
                filename = info.filename
                linenumber = info.linenumber
                # need to evaluate the formatStr and parameters to produce a new string!
                try:
                    paramsNeeded = info.formatStr.count("%")
                    params = []
                    for i in range(0,min(paramsNeeded,4)):
                        try:
                            value = int(msg.GetParameters(i))
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
                text = str(formatStringId) +"("
                for i in range(0,4):
                    try:
                        text += str(msg.GetParameters(i))+","
                    except struct.error:
                        pass
                if text.endswith(","):
                    text = text[:-1]
                text += ")"
                    
        msgStringList.append(str(priority))
        msgStringList.append(filename)
        msgStringList.append(linenumber)
        msgStringList.append(text)

        msgItem = QtWidgets.QTreeWidgetItem(None,msgStringList)
        color = 0
        if(priority == "Error"):
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
        oldPriority = self.msgWidgets[deviceID][streamID].priority
        if priorityInt < oldPriority:
            index = self.tabWidget.indexOf(self.msgWidgets[deviceID][streamID])
            if color == 0:
                color = QtCore.Qt.darkGreen
            self.tabWidget.tabBar().setTabTextColor(index, color)
            self.msgWidgets[deviceID][streamID].priority = priorityInt
        
        self.msgWidgets[deviceID][streamID].addTopLevelItem(msgItem)
        if(self.autoscroll):
            self.msgWidgets[deviceID][streamID].scrollToItem(msgItem)
        # we should have an option to log PrintfID messages as text, or else we should
        # send them out as Printf messages (as long as they don't go to the device!),
        # so standard logs will show them in an easy to read form

    def tabChanged(self, index):
        # when user selects a tab, change it's color back to black
        w = self.tabWidget.widget(index)
        w.priority = 1000
        self.tabWidget.tabBar().setTabTextColor(index, QtCore.Qt.black)

    def fileChanged(self, path):
        for deviceID in range(0, len(self.formatStringFilenames)):
            if self.formatStringFilenames[deviceID] == path:
                self.ReadDictionary(deviceID, self.formatStringFilenames[deviceID])
                print("dictionary " + path + " found at deviceID " + str(deviceID))
                self.statusUpdate.emit("updating DeviceID " + str(deviceID))
                QtCore.QTimer.singleShot(3000, self.clearStatus)
                return
        print("dictionary " + path + " not found")
    def clearStatus(self):
        self.status.setText("")

class DebugPrint(msgtools.lib.gui.Gui):
    def __init__(self, args, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Debug Print 0.1", args, parent)

        self.debugWidget = MsgDebugWidget(sys.argv)
        self.setCentralWidget(self.debugWidget)
        self.debugWidget.messageOutput.connect(self.SendMsg)
        
        # menu items to change view
        clearAction = QtWidgets.QAction('&Clear', self)
        clearAllAction = QtWidgets.QAction('Clear &All', self)
        self.scrollAction = QtWidgets.QAction('&Scroll', self)
        self.scrollAction.setCheckable(1)
        self.scrollAction.setChecked(self.debugWidget.autoscroll)

        menubar = self.menuBar()
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(clearAction)
        viewMenu.addAction(clearAllAction)
        viewMenu.addAction(self.scrollAction)

        clearAction.triggered.connect(self.debugWidget.clearTab)
        clearAllAction.triggered.connect(self.debugWidget.clearAllTabs)
        self.scrollAction.triggered.connect(self.debugWidget.switchScroll)

        # event-based way of getting messages
        self.RxMsg.connect(self.debugWidget.ProcessMessage)

def main():
    # Setup a command line processor...
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('dictionaryfile', nargs='?', default=None, help='''The dictionary file
you want tolook up format string IDs in.''')
    parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    msgApp = DebugPrint(args)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
