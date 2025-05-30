import sys
import datetime
import inspect
import argparse
import json

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork

from .app import *

import msgtools.lib.msgcsv as msgcsv
import msgtools.lib.txtreewidget as txtreewidget

# Tree widget item with support for sorting by a column, and support for per-column editability
# For per-column editability to work, you need to setItemDelegate(NoEditDelegate), and
# NoEditDelegate is defined in txtreewidget.py
class TreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, stringList):
        QtWidgets.QTreeWidgetItem.__init__(self, stringList)
        self.editable = False
        self.editable_columns = {}

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)

    def makeEditable(self, editable_columns):
        self.editable = True
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        for c in editable_columns:
            self.editable_columns[c] = True

    def editableColumn(self, column):
        if not self.editable:
            return False
        if column in self.editable_columns:
            return True
        return False

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

# text widget that allows us to push msg data directly into the text fields
class MsgTextWidget(QtWidgets.QWidget):
    def __init__(self, msgClass, allowedFields=[]):
        super(MsgTextWidget, self).__init__()
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        from msgtools.lib.unknownmsg import UnknownMsg
        if msgClass == UnknownMsg:
            self.showHeader = True
        else:
            self.showHeader = False
        self.allowedFields = dict((fieldName,True) for fieldName in allowedFields)
        tableHeader = []
        if self.fieldAllowed("Time"):
            timeUnits = Messaging.findFieldInfo(Messaging.hdr.fields, "Time").units
            if timeUnits == "ms":
                timeUnits = "s"
            tableHeader.append("Time ("+timeUnits+")")
        if self.showHeader:
            for fieldInfo in Messaging.hdr.fields:
                if len(fieldInfo.bitfieldInfo) == 0:
                    if self.fieldAllowed(fieldInfo.name):
                        tableHeader.append(fieldInfo.name)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        if self.fieldAllowed(bitInfo.name):
                            tableHeader.append(bitInfo.name)
        for fieldInfo in msgClass.fields:
            if self.fieldAllowed(fieldInfo.name):
                tableHeader.append(fieldInfo.name)
            for bitInfo in fieldInfo.bitfieldInfo:
                if self.fieldAllowed(bitInfo.name):
                    tableHeader.append(bitInfo.name)
        self.setHeaderLabels(tableHeader)
    
    def fieldAllowed(self, fieldName):
        if len(self.allowedFields) == 0:
            return True
        return fieldName in self.allowedFields

    def setHeaderLabels(self, headerLabels):
        i = 0
        for h in headerLabels:
            self.grid.addWidget(QtWidgets.QLabel(h), 0, i)
            self.grid.addWidget(QtWidgets.QLabel(''), 1, i)
            i += 1
    
    def setDataLabels(self, dataLabels, dataAlerts):
        i = 0
        for t in dataLabels:
            self.grid.itemAtPosition(1,i).widget().setText(t)
            if dataAlerts[i]:
                #TODO Change text color
                pass
            i += 1

    def addData(self, msg, autoscroll=True):
        msgStringList = []
        columnAlerts = []
        if self.fieldAllowed("Time"):
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
        if self.showHeader:
            for fieldInfo in Messaging.hdr.fields:
                if len(fieldInfo.bitfieldInfo) == 0:
                    if self.fieldAllowed(fieldInfo.name):
                        fieldValue = str(Messaging.get(msg.hdr, fieldInfo))
                        msgStringList.append(fieldValue)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        if self.fieldAllowed(bitInfo.name):
                            fieldValue = str(Messaging.get(msg.hdr, bitInfo))
                            msgStringList.append(fieldValue)
        for fieldInfo in type(msg).fields:
            if(fieldInfo.count == 1):
                if self.fieldAllowed(fieldInfo.name):
                    fieldValue = str(Messaging.get(msg, fieldInfo))
                    msgStringList.append(fieldValue)
                    columnAlerts.append(Messaging.getAlert(msg, fieldInfo))
                for bitInfo in fieldInfo.bitfieldInfo:
                    if self.fieldAllowed(bitInfo.name):
                        fieldValue = str(Messaging.get(msg, bitInfo))
                        msgStringList.append(fieldValue)
                        columnAlerts.append(Messaging.getAlert(msg, bitInfo))
            else:
                if self.fieldAllowed(fieldInfo.name):
                    columnText = ""
                    alert = False
                    for i in range(0,fieldInfo.count):
                        fieldValue = str(Messaging.get(msg, fieldInfo, i))
                        # if the value is what is given when we go off the end of an array, break.
                        if fieldInfo.type == "int" and fieldValue == "UNALLOCATED":
                            break
                        columnText += str(fieldValue)
                        if Messaging.getAlert(msg, fieldInfo, i):
                            alert = True
                        if(i<fieldInfo.count-1):
                            columnText += ", "
                    msgStringList.append(columnText)
                    columnAlerts.append(alert)

        self.setDataLabels(msgStringList, columnAlerts)

# tree widget that allows us to push msg data directly into the tree
class MsgTreeWidget(TreeWidget):
    ROWS_TO_DELETE = 50
    ARRAY_STRING_MAX_LENGTH = 64
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
        self.header().sectionClicked.connect(self.tableHeaderClicked)

        # Use a timer to autoscroll, to reduce CPU usage and make it a little
        # easier to read the screen while it's scrolling.
        self.scrollTimer = QtCore.QTimer()
        self.scrollTimer.setInterval(500)
        self.scrollTimer.setSingleShot(True)
        self.scrollTimer.timeout.connect(self.scrollToBottom)

        self.maxRows = maxRows
        if rowsToDelete > maxRows:
            rowsToDelete = maxRows
        self.rowsToDelete = rowsToDelete

        # key field for our message, that we display one row per value of
        self.keyField = keyField

        self.firstTimeDataAdded = True

    def addData(self, msg, autoscroll=True):
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
                alert = False
                if "hex" == fieldInfo.units.lower():
                    columnText = "0x"
                    for i in range(0, fieldInfo.count):
                        fieldValue = Messaging.get(msg, fieldInfo, i).replace("0x","")
                        if fieldInfo.type == "int" and fieldValue == "UNALLOCATED":
                            break
                        columnText += fieldValue
                        if len(columnText) > MsgTreeWidget.ARRAY_STRING_MAX_LENGTH:
                            columnText += "..."
                            break
                else:
                    for i in range(0,fieldInfo.count):
                        fieldValue = str(Messaging.get(msg, fieldInfo, i))
                        # if the value is what is given when we go off the end of an array, break.
                        if fieldInfo.type == "int" and fieldValue == "UNALLOCATED":
                            break
                        columnText += str(fieldValue)
                        if Messaging.getAlert(msg, fieldInfo, i):
                            alert = True
                        if(i<fieldInfo.count-1):
                            columnText += ", "
                msgStringList.append(columnText)
                columnAlerts.append(alert)
                columnCounter += 1

        msgItem = TreeWidgetItem(msgStringList)
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
            foundAndReplaced = False
            for i in range(0, self.topLevelItemCount()):
                item = self.topLevelItem(i)
                if item.text(keyColumn) == keyValue:
                    foundAndReplaced = True
                    self.takeTopLevelItem(i)
                    self.insertTopLevelItem(i, msgItem)
            if not foundAndReplaced:
                self.addTopLevelItem(msgItem)
                self.sortItems(keyColumn, QtCore.Qt.AscendingOrder)
        else:
            self.addTopLevelItem(msgItem)
            if autoscroll and not self.scrollTimer.isActive():
                self.scrollTimer.start()

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
        self.firstTimeDataAdded = False
        
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
    autocompleted   = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(MsgCommandWidget, self).__init__()
        self.textBox = QtWidgets.QPlainTextEdit()
        self.textBox.setReadOnly(True)
        self.lastHtml = False
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
            self.autocompleted.emit(autocomplete)
        if help:
            self.addText('\n'+help+'\n>\n')

    def returnPressed(self):
        lineOfText = self.lineEdit.text()
        self.addText(lineOfText)
        try:
            msg = msgcsv.csvToMsg(lineOfText)
            if msg:
                self.messageEntered.emit(msg)
                self.addText(" -> Msg\n")
            else:
                self.commandEntered.emit(lineOfText)
        except Exception as e:
            self.addText(repr(e))
        self.lineEdit.setText("")

    def addText(self, text, errorKnown=0):
        lines = text.splitlines()
        for i in range(len(lines)):
            line = lines[i]
            if i < len(lines)-1:
                line = line + '\n'
            elif i == len(lines)-1 and text.endswith('\n'):
                line = line + '\n'
            self.addLine(line, errorKnown)
    
    def addLine(self, line, errorKnown):
        if errorKnown == 2 or 'error' in line.lower() or 'fail' in line.lower():
            self.textBox.appendHtml('<font color="red">'+line+'</font>')
            self.lastHtml = True
        elif errorKnown == 1 or 'warning' in line.lower():
            self.textBox.appendHtml('<font color="orange">'+line+'</font>')
            self.lastHtml = True
        else:
            if self.lastHtml:
                self.textBox.appendHtml('<font color="black"> </font>')
            self.textBox.moveCursor (QtGui.QTextCursor.End)
            self.textBox.insertPlainText(line)
            self.textBox.moveCursor (QtGui.QTextCursor.End)
            self.lastHtml = False

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

    def saveStateStructure(self):
        return self.lineEdit.commandHistory

    def restoreStateStructure(self, state):
        if state:
            for h in state:
                self.lineEdit.addToHistory(h)

class Gui(App, QtWidgets.QMainWindow):
    connectionNameChanged = QtCore.pyqtSignal()
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
            self.connectMenu = menubar.addMenu('&Connect')
            self.connectMenu.addAction(connectAction)
            self.connectMenu.addAction(disconnectAction)
            connectAction.triggered.connect(self.chooseHost)
            disconnectAction.triggered.connect(self.CloseConnection)
    
    def delayedInit(self):
        # Call our readSettings(), then call on_open() if it exists.
        # This order will let subclass override our window state and geometry.
        self.readSettings()
        if hasattr(self.__class__, 'on_open'):
            self.on_open()

    # open dialog box to choose host to connect to
    def chooseHost(self):
        userInput, ok = QInputDialog.getText(self, 'Connect',  'Server:', QLineEdit.Normal, self.connectionName)
        if ok:
            self.connectionName = userInput
            self.OpenConnection()
            self.connectionNameChanged.emit()
    
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

import re
def get_trailing_number(s):
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else None

def rchop(s, suffix):
    if suffix and s.endswith(suffix):
        return s[:-len(suffix)]
    return s

def get_type(s):
    type_names = {"_f":"float", "_u":"uint32", "_i":"int32"}
    if s.endswith(tuple(type_names.keys())):
        return type_names[s[-2:]]
    else:
        return ""

def get_name_type_and_count(s):
    count = get_trailing_number(s)
    if count != None:
        s = rchop(s, str(count))
    else:
        count = 1
    type = get_type(s)
    name = s[:-2]
    return name, type, count

class ConfigTreeWidgetItem(TreeWidgetItem):
    NAME_COLUMN = 0
    TYPE_COLUMN = 1
    DEVICE_VALUE_COLUMN = 2
    SYNC_COLUMN = 3
    FILE_VALUE_COLUMN = 4
    COLUMN_COUNT = 5
    def __init__(self, key):
        name, type, count = get_name_type_and_count(key)
        if count == 1:
            type_string = type
        else:
            type_string = "%s[%s]" % (type, count)
        string_list = [name, type_string, "", "", ""]
        super().__init__(string_list)
        self.makeEditable([ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN, ConfigTreeWidgetItem.FILE_VALUE_COLUMN])
        
        self.key = key
        self.name = name
        self.type = type
        self.count = count
        
        self.device_value = None
        self.file_value = None
        sync_left = QtWidgets.QToolButton()
        sync_left.setText("\u2190")
        sync_right = QtWidgets.QToolButton()
        sync_right.setText("\u2192")
        self.sync_widget = QtWidgets.QWidget()
        self.sync_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(sync_left)
        hbox.addWidget(sync_right)
        self.sync_widget.setLayout(hbox)
        sync_left.clicked.connect(self.syncLeft)
        sync_right.clicked.connect(self.syncRight)

    def data(self, column, role):
        if role != QtCore.Qt.FontRole and role != QtCore.Qt.ForegroundRole:
            return super(ConfigTreeWidgetItem, self).data(column, role)

        if column == ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN:
            alert = self.device_value != self.text(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN)
            alert_color = QtGui.QColor("darkOrange")
        elif column == ConfigTreeWidgetItem.FILE_VALUE_COLUMN:
            alert = self.file_value != self.text(ConfigTreeWidgetItem.FILE_VALUE_COLUMN)
            alert_color = QtGui.QColor("darkOrange")
        else:
            device_value = self.text(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN)
            file_value = self.text(ConfigTreeWidgetItem.FILE_VALUE_COLUMN)
            alert = False if device_value == file_value else True
            alert_color = QtCore.Qt.red
        if alert:
            self.treeWidget().alert.emit(alert_color)
        if role == QtCore.Qt.FontRole:
            font = QtGui.QFont()
            if alert:
                font.setBold(True)
            return font
        if role == QtCore.Qt.ForegroundRole:
            brush = QtGui.QBrush()
            if alert:
                brush.setColor(alert_color)
            return brush

        return super(ConfigTreeWidgetItem, self).data(column, role)

    def syncLeft(self):
        self.setText(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN, self.text(ConfigTreeWidgetItem.FILE_VALUE_COLUMN))

    def syncRight(self):
        self.setText(ConfigTreeWidgetItem.FILE_VALUE_COLUMN, self.text(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN))
    
    def setDeviceValue(self, value):
        self.device_value = value
        self.setText(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN, value)

    def setFileValue(self, value):
        self.file_value = value
        self.setText(ConfigTreeWidgetItem.FILE_VALUE_COLUMN, value)

# Tree widget that synchronizes configuration settings between a device and a config file,
# and lets the user edit both.
class ConfigTreeWidget(TreeWidget):
    send_msg = QtCore.pyqtSignal(object)
    alert = QtCore.pyqtSignal(object)
    ARRAY_STRING_MAX_LENGTH = 64
    def __init__(self, msg_namespace, cfg_filename):
        super(ConfigTreeWidget, self).__init__()
        self.msg_namespace = msg_namespace
        self.cfg_filename = cfg_filename

        # add table header, one column for each message field
        tableHeader = []
        tableHeader.append("Setting Name")
        tableHeader.append("Type")
        tableHeader.append("Device Value")
        tableHeader.append("Sync")
        tableHeader.append("File Value")
        self.setHeaderLabels(tableHeader)
        
        self.items_by_key = {}
        for key, value in self.msg_namespace.GetConfigValue.ConfigSettingsKeys.items():
            # Don't use value 0, it's a marker for an Invalid value.
            if value == 0:
                continue
            tree_item = ConfigTreeWidgetItem(key)
            self.addTopLevelItem(tree_item)
            self.setItemDelegate(txtreewidget.NoEditDelegate(self, self))
            self.items_by_key[key] = tree_item
            self.setItemWidget(tree_item, ConfigTreeWidgetItem.SYNC_COLUMN, tree_item.sync_widget)

        for c in range(ConfigTreeWidgetItem.COLUMN_COUNT):
            self.resizeColumnToContents(c)
    
    def load_from_device(self):
        query_msg = self.msg_namespace.GetConfigKeys()
        self.send_msg.emit(query_msg)

    def save_to_device(self):
        for key, tree_item in self.items_by_key.items():
            values = tree_item.text(ConfigTreeWidgetItem.DEVICE_VALUE_COLUMN)
            if values == "":
                delete_value_msg = self.msg_namespace.DeleteConfigValue()
                delete_value_msg.SetKey(key)
                self.send_msg.emit(delete_value_msg)
            else:
                set_value_msg = self.msg_namespace.SetConfigValue()
                set_value_msg.SetKey(key)
                idx = 0
                for value in values.split(","):
                    set_value_msg.SetValues(float(value), idx)
                    idx += 1
                set_value_msg.SetCount(idx)
                self.send_msg.emit(set_value_msg)
        # After saving to device, re-load from the device
        self.load_from_device()

    def process_msg(self, msg):
        if type(msg) == self.msg_namespace.CurrentConfigKeys:
            # if we got a message with a list of config setting keys,
            # iterate through the keys and request the config setting for each.
            for i in range(msg.GetCount()):
                query_msg = self.msg_namespace.GetConfigValue()
                query_msg.SetKey(msg.GetKey(i))
                self.send_msg.emit(query_msg)

        elif type(msg) == self.msg_namespace.CurrentConfigValue:
            # if we got a message with the value of a config setting,
            # display it in the table, unless it's an invalid key
            key_int = msg.GetKey(enumAsInt=True)
            key = msg.GetKey()
            if key == "Invalid" or key_int == 0:
                return
            if key in self.items_by_key:
                count = msg.GetCount()
                value = ""
                for i in range(count):
                    value += str(msg.GetValues(i)) + ", "
                value = value[:-2]
                tree_item = self.items_by_key[key]
                tree_item.setDeviceValue(value)
                self.viewport().update()
            else:
                print("Key %s not in keys %s" % (key, list(self.items_by_key.keys())))

    def load_from_file(self):
        with open(self.cfg_filename, 'r') as f:
            for line in f:
                data = json.loads(line)
                for key, value in data.items():
                    try:
                        tree_item = self.items_by_key[key]
                        tree_item.setFileValue(value)
                    except KeyError:
                        print("ERROR! Invalid Key %s not in %s" % (key, self.items_by_key.keys()))
        self.viewport().update()

    def save_to_file(self):
        with open(self.cfg_filename, 'w') as f:
            for key, tree_item in self.items_by_key.items():
                value = tree_item.text(ConfigTreeWidgetItem.FILE_VALUE_COLUMN)
                if value:
                    d = {key: value}
                    f.write(json.dumps(d)+"\n")
        # After writing, re-read the file.
        self.load_from_file()

class ConfigEditor(QtWidgets.QWidget):
    send_msg = QtCore.pyqtSignal(object)
    alert = QtCore.pyqtSignal(object)
    def __init__(self, msg_namespace, cfg_filename):
        super(ConfigEditor, self).__init__()

        hbox = QtWidgets.QHBoxLayout()
        load_from_device_button = QtWidgets.QPushButton("Load from device")
        save_to_device_button = QtWidgets.QPushButton("Save to device")
        load_from_file_button = QtWidgets.QPushButton("Load from file")
        save_to_file_button = QtWidgets.QPushButton("Save to file")
        hbox.addWidget(load_from_device_button)
        hbox.addWidget(save_to_device_button)
        hbox.addWidget(load_from_file_button)
        hbox.addWidget(save_to_file_button)

        self.edit_tree = ConfigTreeWidget(msg_namespace, cfg_filename)
        self.edit_tree.send_msg.connect(self.send_msg)
        self.edit_tree.alert.connect(self.alert)

        load_from_file_button.clicked.connect(self.edit_tree.load_from_file)
        load_from_device_button.clicked.connect(self.edit_tree.load_from_device)
        save_to_file_button.clicked.connect(self.edit_tree.save_to_file)
        save_to_device_button.clicked.connect(self.edit_tree.save_to_device)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.edit_tree)
        self.setLayout(vbox)
    
    def process_msg(self, msg):
        self.edit_tree.process_msg(msg)
    