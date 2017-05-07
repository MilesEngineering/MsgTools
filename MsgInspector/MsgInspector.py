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

class TreeWidget(QtWidgets.QTreeWidget):
    def keyPressEvent(self, keyEvent):
        if keyEvent.matches(QtGui.QKeySequence.Copy):
            self.copySelection()
        else:
            super(TreeWidget, self).keyPressEvent(keyEvent)

    def copySelection(self):
        selectedItems = self.selectedItems()
        copiedText = ""
        h = self.headerItem()
        for col in range(h.columnCount()):
            if col != 0:
                copiedText += ", "
            copiedText += h.text(col)
        copiedText += "\n"
        
        for itemNumber in range(len(selectedItems)):
            w = selectedItems[itemNumber]
            for col in range(w.columnCount()):
                if col != 0:
                    copiedText += ", "
                copiedText += w.text(col)
            copiedText += "\n"
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(copiedText)

    def tableHeaderClicked(self, column):
        tree = self
        header = tree.header()
        fieldName = tree.headerItem().text(column)
        msgName = tree.msgName
        if not msgName in self.inspector.keyFields or self.inspector.keyFields[msgName] != fieldName:
            print("sorting " + msgName + " on " + fieldName)
            header.setSortIndicator(column, QtCore.Qt.AscendingOrder)
            self.inspector.keyFields[msgName] = fieldName
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
            del self.inspector.keyFields[msgName]
            header.setSortIndicator(0, QtCore.Qt.AscendingOrder)

class MsgInspector(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Inspector 0.1", argv, [], parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        self.resize(640, 480)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
        
        # whether we should autoscroll as data is added
        self.autoscroll = 1
        
        # menu items to change view
        clearAction = QtWidgets.QAction('&Clear', self)
        clearAllAction = QtWidgets.QAction('Clear &All', self)
        self.scrollAction = QtWidgets.QAction('&Scroll', self)
        self.scrollAction.setCheckable(1)
        self.scrollAction.setChecked(self.autoscroll)

        menubar = self.menuBar()
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(clearAction)
        viewMenu.addAction(clearAllAction)
        viewMenu.addAction(self.scrollAction)

        clearAction.triggered.connect(self.clearTab)
        clearAllAction.triggered.connect(self.clearAllTabs)
        self.scrollAction.triggered.connect(self.switchScroll)
    
    def clearTab(self):
        self.tabWidget.currentWidget().clear()
    
    def clearAllTabs(self):
        for id, widget in self.msgWidgets.items():
            widget.clear()
        
    def switchScroll(self):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def tableDataDoubleClicked(self, treeWidgetItem, column):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def ProcessMessage(self, msg):
        hdr = msg.hdr
        id       = hex(hdr.GetMessageID())
        msgName = msg.MsgName()

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
            msgWidget = TreeWidget()
            msgWidget.inspector = self
            msgWidget.itemDoubleClicked.connect(self.tableDataDoubleClicked)
            msgWidget.msgName = msgName
            msgWidget.setSelectionMode(msgWidget.ContiguousSelection)
            msgWidget.setSelectionBehavior(msgWidget.SelectRows)
            # configure the header so we can click on it to sort
            header = msgWidget.header()
            header.setSectionsClickable(1)
            header.setSortIndicatorShown(1)
            # show sort indicator ascending on Time, if not sorting, because we append incoming messages
            header.setSortIndicator(0, QtCore.Qt.AscendingOrder)
            header.myTreeWidget = msgWidget
            header.sectionClicked.connect(msgWidget.tableHeaderClicked)
            
            # add it to the tab widget, so the user can see it
            self.tabWidget.addTab(msgWidget, msgName)
            
            # add table header, one column for each message field
            tableHeader = []
            tableHeader.append("Time (ms)")
            for fieldInfo in type(msg).fields:
                tableHeader.append(fieldInfo.name)
                for bitInfo in fieldInfo.bitfieldInfo:
                    tableHeader.append(bitInfo.name)
            
            msgWidget.setHeaderLabels(tableHeader)
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[id] = msgWidget
        
        msgStringList = []
        columnAlerts = []
        try:
            msgStringList.append(str(msg.hdr.GetTime()))
        except AttributeError:
            msgStringList.append("Unknown")
        columnAlerts.append(0)
        keyColumn = -1
        columnCounter = 1
        for fieldInfo in type(msg).fields:
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
                    # if the value is what is given when we go off the end of an array, break.
                    if fieldInfo.type == "int" and fieldValue == "UNALLOCATED":
                        break
                    columnText += str(fieldValue)
                    if Messaging.getAlert(msg, fieldInfo, i):
                        alert = 1
                    if(i<fieldInfo.count-1):
                        columnText += ", "
                msgStringList.append(columnText)
                columnAlerts.append(alert)
                columnCounter += 1

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
            if(self.autoscroll):
                self.msgWidgets[id].scrollToItem(msgItem)
        if firstTime:
            count = 0
            for fieldInfo in type(msg).fields:
                msgWidget.resizeColumnToContents(count)
                count += 1


# main starts here
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
