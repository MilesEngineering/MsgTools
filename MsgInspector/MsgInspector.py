#!/usr/bin/env python3
import struct
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class TreeWidgetItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, parent, stringList):
        QtWidgets.QTreeWidgetItem.__init__(self, parent, stringList)

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)

class MsgInspector(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Inspector 0.1", argv, [], parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ShowMessage)

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        self.resize(640, 480)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
    
    def tableHeaderClicked(self, column):
        header = self.sender()
        tree = header.myTreeWidget
        fieldName = tree.headerItem().text(column)
        msgName = tree.msgName
        if not msgName in self.keyFields or self.keyFields[msgName] != fieldName:
            print("sorting " + msgName + " on " + fieldName)
            header.setSortIndicator(column, QtCore.Qt.AscendingOrder)
            self.keyFields[msgName] = fieldName
            tree.sortItems(column, QtCore.Qt.AscendingOrder)
            valueToRemove = None
            for i in range(tree.topLevelItemCount()-1, -1 ,-1):
                item = tree.topLevelItem(i)
                if not valueToRemove == None and item.text(column) == valueToRemove:
                    tree.takeTopLevelItem(i)
                else:
                    valueToRemove = item.text(column)
        else:
            print("not sorting " + msgName)
            del self.keyFields[msgName]
            header.setSortIndicator(0, QtCore.Qt.AscendingOrder)

    def ShowMessage(self, msg):
        # default to NOT printing body as hex
        printBodyAsHex = 0
        # read the ID, and get the message name, so we can print stuff about the body
        id       = hex(Messaging.hdr.GetMessageID(msg))
        if not id in Messaging.MsgNameFromID:
            printBodyAsHex = 1
            if(not(id in self.msgWidgets)):
                print("WARNING! No definition for ", id, ", only displaying header!\n")
            #return
            msgName = "unknown "+id
            msgClass = Messaging.hdr
        else:
            msgName = Messaging.MsgNameFromID[id]
            msgClass = Messaging.MsgClassFromName[msgName]

        if(msgClass == None):
            print("WARNING!  No definition for ", id, "!\n")
            return

        replaceMode = 0
        if self.allowedMessages:
            if not msgName in self.allowedMessages:
                return
        if msgName in self.keyFields:
            replaceMode = 1

        firstTime = 0
        if(not(id in self.msgWidgets)):
            firstTime = 1
            # create a new tree widget
            msgWidget = QtWidgets.QTreeWidget()
            msgWidget.msgName = msgName
            # configure the header so we can click on it to sort
            header = msgWidget.header()
            header.setSectionsClickable(1)
            header.setSortIndicatorShown(1)
            # show sort indicator ascending on Time, if not sorting, because we append incoming messages
            header.setSortIndicator(0, QtCore.Qt.AscendingOrder)
            header.myTreeWidget = msgWidget
            header.sectionClicked.connect(self.tableHeaderClicked)
            
            # add it to the tab widget, so the user can see it
            self.tabWidget.addTab(msgWidget, msgName)
            
            # add table header, one column for each message field
            tableHeader = []
            tableHeader.append("Time (ms)")
            for fieldInfo in msgClass.fields:
                tableHeader.append(fieldInfo.name)
                for bitInfo in fieldInfo.bitfieldInfo:
                    tableHeader.append(bitInfo.name)
            if printBodyAsHex:
                tableHeader.append("Body")
            
            msgWidget.setHeaderLabels(tableHeader)
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[id] = msgWidget
        
        msgStringList = []
        columnAlerts = []
        try:
            msgStringList.append(str(Messaging.hdr.GetTime(msg)))
        except AttributeError:
            msgStringList.append("Unknown")
        columnAlerts.append(0)
        keyColumn = -1
        columnCounter = 1
        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                fieldValue = str(Messaging.get(msg, fieldInfo))
                msgStringList.append(fieldValue)
                columnAlerts.append(Messaging.getAlert(msg, fieldInfo))
                if replaceMode and fieldInfo.name == self.keyFields[msgName]:
                    keyValue = fieldValue
                    keyColumn = columnCounter
                columnCounter += 1
                for bitInfo in fieldInfo.bitfieldInfo:
                    fieldValue = str(Messaging.get(msg, bitInfo))
                    msgStringList.append(fieldValue)
                    columnAlerts.append(Messaging.getAlert(msg, bitInfo))
                    if replaceMode and bitInfo.name == self.keyFields[msgName]:
                        keyValue = fieldValue
                        keyColumn = columnCounter
                    columnCounter += 1
            else:
                columnText = ""
                alert = 0
                for i in range(0,fieldInfo.count):
                    fieldValue = Messaging.get(msg, fieldInfo, i)
                    columnText += str(fieldValue)
                    if Messaging.getAlert(msg, fieldInfo, i):
                        alert = 1
                    if(i<fieldInfo.count-1):
                        columnText += ", "
                msgStringList.append(columnText)
                columnAlerts.append(alert)
                columnCounter += 1
        if printBodyAsHex:
            value = "0x"
            for i in range(Messaging.hdrSize, len(msg)):
                value += " " + format(struct.unpack_from('B', msg, i)[0], '02x')
            msgStringList.append(value)

        msgItem = TreeWidgetItem(None,msgStringList)
        for column in range(0, len(columnAlerts)):
            if columnAlerts[column]:
                font = msgItem.font(column)
                brush = msgItem.foreground(column)
                font.setBold(1)
                brush.setColor(QtCore.Qt.red)
                msgItem.setFont(column, font)
                msgItem.setForeground(column, brush)
                msgItem.setBackground(column, brush)
        if replaceMode and keyColumn >= 0:
            # find row that has key field that matches ours
            foundAndReplaced = 0
            for i in range(0, self.msgWidgets[id].topLevelItemCount()):
                item = self.msgWidgets[id].topLevelItem(i)
                if item.text(keyColumn) == keyValue:
                    foundAndReplaced = 1
                    self.msgWidgets[id].takeTopLevelItem(i)
                    self.msgWidgets[id].insertTopLevelItem(i, msgItem)
            if not foundAndReplaced:
                self.msgWidgets[id].addTopLevelItem(msgItem)
                self.msgWidgets[id].sortItems(keyColumn, QtCore.Qt.AscendingOrder)
        else:
            self.msgWidgets[id].addTopLevelItem(msgItem)
        if firstTime:
            count = 0
            for fieldInfo in msgClass.fields:
                msgWidget.resizeColumnToContents(count)
                count += 1


# main starts here
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
