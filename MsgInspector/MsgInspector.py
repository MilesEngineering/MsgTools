#!/usr/bin/env python3
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class MsgInspector(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Inspector 0.1", argv, parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ShowMessage)

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        self.resize(640, 480)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}

    def ShowMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        id       = hex(Messaging.hdr.GetID(msg))
        msgName = Messaging.MsgNameFromID[id]
        msgClass = Messaging.MsgClassFromName[msgName]

        if(msgClass == None):
            print("WARNING!  No definition for ", id, "!\n")
            return

        firstTime = 0
        if(not(id in self.msgWidgets)):
            firstTime = 1
            # create a new tree widget
            msgWidget = QtGui.QTreeWidget()
            
            # add it to the tab widget, so the user can see it
            self.tabWidget.addTab(msgWidget, msgName)
            
            # add table header, one column for each message field
            tableHeader = []
            tableHeader.append("Time (ms)")
            for fieldInfo in msgClass.fields:
                tableHeader.append(fieldInfo.name)
                for bitInfo in fieldInfo.bitfieldInfo:
                    tableHeader.append(bitInfo.name)
            
            msgWidget.setHeaderLabels(tableHeader)
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[id] = msgWidget
        
        msgStringList = []
        msgStringList.append(str(Messaging.hdr.GetTime(msg)))
        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                msgStringList.append(str(Messaging.get(msg, fieldInfo)))
                for bitInfo in fieldInfo.bitfieldInfo:
                    msgStringList.append(str(Messaging.get(msg, bitInfo)))
            else:
                columnText = ""
                for i in range(0,fieldInfo.count):
                    columnText += str(Messaging.get(msg, fieldInfo, i))
                    if(i<fieldInfo.count-1):
                        columnText += ", "
                msgStringList.append(columnText)
        msgItem = QTreeWidgetItem(None,msgStringList)
        self.msgWidgets[id].addTopLevelItem(msgItem)
        if firstTime:
            count = 0
            for fieldInfo in msgClass.fields:
                msgWidget.resizeColumnToContents(count)
                count += 1

# main starts here
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
