import sys

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork

from MsgApp import *

# tree widget item with support for sorting by a column
class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, stringList):
        QtWidgets.QTreeWidgetItem.__init__(self, parent, stringList)

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)

# tree widget that we can copy-and-paste on
class TreeWidget(QtWidgets.QTreeWidget):
    def __init__(self):
        super(TreeWidget, self).__init__() # what constructor parameters?!
        self.setSelectionMode(self.ContiguousSelection)
        self.setSelectionBehavior(self.SelectRows)

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

# tree widget that allows us to push msg data directly into the tree
class MsgTreeWidget(TreeWidget):
    MAX_ROWS = 1000
    ROWS_TO_DELETE = 50
    def __init__(self, msgClass, keyField=None, maxRows=1000, rowsToDelete=50):
        super(MsgTreeWidget, self).__init__()
        # add table header, one column for each message field
        tableHeader = []
        tableHeader.append("Time (ms)")
        for fieldInfo in msgClass.fields:
            tableHeader.append(fieldInfo.name)
            for bitInfo in fieldInfo.bitfieldInfo:
                tableHeader.append(bitInfo.name)
        self.setHeaderLabels(tableHeader)
        # configure the header so we can click on it to sort
        self.header().setSectionsClickable(1)
        self.header().setSortIndicatorShown(1)
        # show sort indicator ascending on Time, if not sorting, because we append incoming messages
        self.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.header().myTreeWidget = self
        self.header().sectionClicked.connect(self.tableHeaderClicked)
        
        self.maxRows = maxRows
        if rowsToDelete > maxRows:
            rowsToDelete = maxRows
        self.rowsToDelete = rowsToDelete

        # key field for our message, that we display one row per value of
        self.keyField = keyField

        self.firstTimeDataAdded = 1

    def addData(self, msg, autoscroll=1):
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
                if fieldInfo.name == self.keyField:
                    keyValue = fieldValue
                    keyColumn = columnCounter
                columnCounter += 1
                for bitInfo in fieldInfo.bitfieldInfo:
                    fieldValue = str(Messaging.get(msg, bitInfo))
                    msgStringList.append(fieldValue)
                    columnAlerts.append(Messaging.getAlert(msg, bitInfo))
                    if bitInfo.name == self.keyField:
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
        if self.keyField != None and keyColumn >= 0:
            # find row that has key field that matches ours
            foundAndReplaced = 0
            for i in range(0, self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.text(keyColumn) == keyValue:
                    foundAndReplaced = 1
                    self.takeTopLevelItem(i)
                    self.insertTopLevelItem(i, msgItem)
            if not foundAndReplaced:
                self.addTopLevelItem(msgItem)
                self.sortItems(keyColumn, QtCore.Qt.AscendingOrder)
        else:
            self.addTopLevelItem(msgItem)
            if(autoscroll):
                self.scrollToItem(msgItem)
            # when deleting, make a bunch of room so that if we're auto scrolling we have a bit of time before it
            # shifts the data.  Otherwise the user can't read stuff if it's going by too fast.
            if self.topLevelItemCount() > self.maxRows:
                for i in range(0, self.rowsToDelete):
                    self.takeTopLevelItem(0)
                    
        if self.firstTimeDataAdded:
            count = 0
            for fieldInfo in type(msg).fields:
                self.resizeColumnToContents(count)
                count += 1
        self.firstTimeDataAdded = 0
        
    def tableHeaderClicked(self, column):
        fieldName = self.headerItem().text(column)
        if self.keyField == None or self.keyField != fieldName:
            self.keyField = fieldName
            self.header().setSortIndicator(column, QtCore.Qt.AscendingOrder)
            self.sortItems(column, QtCore.Qt.AscendingOrder)
            valueToRemove = None
            for i in range(self.topLevelItemCount()-1, -1 ,-1):
                item = self.topLevelItem(i)
                if not valueToRemove == None and item.text(column) == valueToRemove:
                    self.takeTopLevelItem(i)
                else:
                    valueToRemove = item.text(column)
        else:
            self.keyField = None
            self.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)


class MsgGui(MsgApp, QtWidgets.QMainWindow):
    def __init__(self, name, argv, options, parent=None):
        # default to Network, unless we have a input filename that contains .txt
        headerName = "NetworkHeader"
        if any(".txt" in s for s in argv) or any(".TXT" in s for s in argv):
            headerName = "SerialHeader"

        QtWidgets.QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, name, headerName, argv, options)

        # make a status bar to print status messages
        self.status = QtWidgets.QLabel("Initializing")
        self.statusBar().addPermanentWidget(self.status)
        # hook it up to our base class statusUpdate signal
        self.statusUpdate.connect(self.status.setText)

        self.readSettings()
        self.setWindowTitle(self.name)

        # create menu items, connect them to socket operations
        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            connectAction = QtWidgets.QAction('&Connect', self)
            disconnectAction = QtWidgets.QAction('&Disconnect', self)

            menubar = self.menuBar()
            connectMenu = menubar.addMenu('&Connect')
            connectMenu.addAction(connectAction)
            connectMenu.addAction(disconnectAction)
            connectAction.triggered.connect(self.chooseHost)
            disconnectAction.triggered.connect(self.connection. disconnectFromHost)
    
    # open dialog box to choose host to connect to
    def chooseHost(self):
        (hostIp, port) = self.connectionName.split(":")
        if(hostIp == None):
            hostIp = "127.0.0.1"

        if(port == None):
            port = "5678"
        
        port = int(port)

        hostIp, ok = QInputDialog.getText(self, 'Connect',  'Server:', QLineEdit.Normal, hostIp)
        self.connection.connectToHost(hostIp, port)
    
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super(MsgGui, self).closeEvent(event)
    
    def readSettings(self):
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))
        self.restoreState(self.settings.value("windowState", QtCore.QByteArray()))
