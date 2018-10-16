import sys
import datetime
import inspect
import argparse

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork

from .app import *

import msgtools.lib.msgcsv as msgcsv

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
                # treat first column as time, convert HH:MM:SS.sss to a float
                if col == 0:
                    t = w.text(col)
                    if ":" in t:
                        time_components = t.split(':')
                        t = int(time_components[0]) * 3600 + int(time_components[1]) * 60 + float(time_components[2])
                        copiedText += str(t)
                    else:
                        copiedText += str(t)
                else:
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
        from msgtools.lib.unknownmsg import UnknownMsg
        if msgClass == UnknownMsg:
            self.showHeader = True
        else:
            self.showHeader = False
        # add table header, one column for each message field
        tableHeader = []
        timeUnits = Messaging.findFieldInfo(Messaging.hdr.fields, "Time").units
        if timeUnits == "ms":
            timeUnits = "s"
        tableHeader.append("Time ("+timeUnits+")")
        if self.showHeader:
            for fieldInfo in Messaging.hdr.fields:
                if len(fieldInfo.bitfieldInfo) == 0:
                    tableHeader.append(fieldInfo.name)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        tableHeader.append(bitInfo.name)
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
            timeVal = msg.hdr.GetTime()
            timeInfo = Messaging.findFieldInfo(msg.hdr.fields, "Time")
            if timeInfo.units == "ms":
                timeVal = timeVal / 1000.0
            timeVal = datetime.datetime.fromtimestamp(timeVal, datetime.timezone.utc)
        except AttributeError:
            timeVal = datetime.datetime.now()
        timeVal = timeVal.strftime('%H:%M:%S.%f')[:-3]
        msgStringList.append(timeVal)
        columnAlerts.append(0)
        keyColumn = -1
        columnCounter = 1
        if self.showHeader:
            for fieldInfo in Messaging.hdr.fields:
                if len(fieldInfo.bitfieldInfo) == 0:
                    fieldValue = str(Messaging.get(msg.hdr, fieldInfo))
                    msgStringList.append(fieldValue)
                    columnCounter += 1
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        fieldValue = str(Messaging.get(msg.hdr, bitInfo))
                        msgStringList.append(fieldValue)
                        columnCounter += 1
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

class LineEditWithHistory(QtWidgets.QLineEdit):
    tabPressed = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(LineEditWithHistory, self).__init__()
        self.commandHistory = []
        self.placeInHistory = 0

    def setToHistoryItem(self, index):
        self.placeInHistory = index
        if self.placeInHistory > len(self.commandHistory) - 1:
            self.placeInHistory = len(self.commandHistory)
            self.setText('')
        else:
            if self.placeInHistory < 0:
                self.placeInHistory = 0
            try:
                self.setText(self.commandHistory[self.placeInHistory])
            except IndexError:
                self.setText('')
    
    # disable tab focus so we get tab keys delivered via keyPressEvent.
    def focusNextPrevChild(self, next):
        return False
    
    def addToHistory(self, lineOfText):
        if len(self.commandHistory) == 0 or self.commandHistory[-1] != lineOfText:
            self.commandHistory.append(lineOfText)
            if len(self.commandHistory) > 20:
                self.commandHistory.pop(0)
        self.placeInHistory = len(self.commandHistory)

    def keyPressEvent(self, keyEvent):
        if keyEvent.key() == QtCore.Qt.Key_Return:
            # add to history
            self.addToHistory(self.text())
        elif keyEvent.key() == QtCore.Qt.Key_Up:
            #up in history
            self.setToHistoryItem(self.placeInHistory - 1)
        elif keyEvent.key() == QtCore.Qt.Key_Down:
            # down in history
            self.setToHistoryItem(self.placeInHistory + 1)
        elif keyEvent.key() == QtCore.Qt.Key_Tab:
            self.tabPressed.emit()
            return
        super(LineEditWithHistory, self).keyPressEvent(keyEvent)

class MsgCommandWidget(QtWidgets.QWidget):
    commandEntered = QtCore.pyqtSignal(str)
    messageEntered = QtCore.pyqtSignal(object)
    def __init__(self, parent=None):
        super(MsgCommandWidget, self).__init__()
        self.textBox = QtWidgets.QPlainTextEdit()
        self.textBox.setReadOnly(True)
        self.lineEdit = LineEditWithHistory()
        self.lineEdit.returnPressed.connect(self.returnPressed)
        self.lineEdit.tabPressed.connect(self.tabPressed)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.textBox)
        vbox.addWidget(self.lineEdit)
        self.setLayout(vbox)
    
    def tabPressed(self):
        lineOfText = self.lineEdit.text()
        autocomplete, help = msgcsv.csvHelp(lineOfText)
        if autocomplete:
            self.lineEdit.setText(autocomplete)
        if help:
            self.addText('\n'+help+'\n>\n')

    def returnPressed(self):
        lineOfText = self.lineEdit.text()
        self.addText(lineOfText)
        msg = msgcsv.csvToMsg(lineOfText)
        if msg:
            self.messageEntered.emit(msg)
            self.addText(" -> Msg\n")
        else:
            self.commandEntered.emit(lineOfText)
        self.lineEdit.setText("")

    def addText(self, text):
        self.textBox.moveCursor (QtGui.QTextCursor.End)
        self.textBox.insertPlainText(text)
        self.textBox.moveCursor (QtGui.QTextCursor.End)

    def clear(self):
        self.textBox.clear()
    
    def addToHistory(self, lineOfText):
        self.lineEdit.addToHistory(lineOfText)
    
    def saveState(self):
        ret = ""
        for h in self.lineEdit.commandHistory:
            ret = ret + "|" + h
        return ret
    
    def restoreState(self, state):
        if state:
            history = state.split("|")
            for h in history:
                self.lineEdit.addToHistory(h)

class Gui(App, QtWidgets.QMainWindow):
    @classmethod
    def addBaseArguments(cls, parser):
        '''
        Adds base app arguments to the provided ArgParser

        returns the parser
        '''

        # Just delegate - this design choice is two fold - it prevents
        # code using the Gui from including the App as a dependency.
        # It also allows us to inject Gui specific arguments into this
        # base class later.
        return App.addBaseArguments(parser)

    '''Gui base class that provides standard connection and status UI

        name - the name of the app - will be displayed in the title bar of the window
        args - argparse.Namespace representing parsed arguments.  See app.py for
               the standard options provided as part of this Gui/App framework used
               in most MsgTools utilities.
        parent - a parent Qt Widget to attach to
    '''
    def __init__(self, name, args, parent=None):

        QtWidgets.QMainWindow.__init__(self,parent)
        App.__init__(self, name, args)

        # make a status bar to print status messages
        self.status = QtWidgets.QLabel("Initializing")
        self.statusBar().addPermanentWidget(self.status)
        # hook it up to our base class statusUpdate signal
        self.statusUpdate.connect(self.status.setText)
        
        # a checkbox for connection state to the status bar
        self.connectionCheckbox = QtWidgets.QCheckBox("")
        self.statusBar().addPermanentWidget(self.connectionCheckbox)
        # hook it up to connect/disconnect
        self.connectionCheckbox.clicked.connect(self.connectionCheckedChanged)
        self.connectionChanged.connect(self.connectionChangedSlot)

        QtCore.QTimer.singleShot(0, self.delayedInit)
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
            disconnectAction.triggered.connect(self.CloseConnection)
    
    def delayedInit(self):
        if hasattr(self.__class__, 'on_open'):
            self.on_open()
        self.readSettings()

    # open dialog box to choose host to connect to
    def chooseHost(self):
        userInput, ok = QInputDialog.getText(self, 'Connect',  'Server:', QLineEdit.Normal, self.connectionName)
        if ok:
            self.connectionName = userInput
            self.OpenConnection()
    
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        if hasattr(self.__class__, 'on_close'):
            self.on_close()
        super(Gui, self).closeEvent(event)
    
    def readSettings(self):
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))
        self.restoreState(self.settings.value("windowState", QtCore.QByteArray()))

    def connectionChangedSlot(self, connected):
        self.connectionCheckbox.setChecked(connected)
        if connected:
            self.statusUpdate.emit('')
            self.connectionCheckbox.setText("Connected")
        else:
            self.connectionCheckbox.setText("NOT Connected")

    def connectionCheckedChanged(self, checked):
        self.statusUpdate.emit('')
        if checked:
            self.connectionCheckbox.setText("Connecting")
            self.OpenConnection()
        else:
            self.connectionCheckbox.setText("NOT Connected")
            self.CloseConnection()
