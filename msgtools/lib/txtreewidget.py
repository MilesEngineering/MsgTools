#!/cygdrive/c/Python34/python.exe
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from msgtools.lib.messaging import Messaging

class FieldItem(QTreeWidgetItem):
    def __init__(self, editable, tree_widget, msg, msg_key, fieldInfo, column_strings, index):
        if len(column_strings) == 0:
            column_strings = [None, fieldInfo.name, "", fieldInfo.units, fieldInfo.description]
            if index != None:
                column_strings[1] = "    [" + str(index) + "]"
        QTreeWidgetItem.__init__(self, None, column_strings)
        
        self.editable = editable
        self.fieldInfo = fieldInfo
        if index == None:
            self.fieldName = fieldInfo.name
        else:
            self.fieldName = "%s[%d]" % (fieldInfo.name, index)
        self.msg = msg
        self.msg_key = msg_key
        self.index = index

        if self.editable:
            self.setFlags(self.flags() | Qt.ItemIsEditable)
            
            if fieldInfo.type == "enumeration":
                self.overrideWidget = QComboBox()
                self.overrideWidget.addItems(fieldInfo.enum[0].keys())
                self.overrideWidget.activated.connect(self.overrideWidgetValueChanged)
                # there's some odd behavior in the UI when the box is editable :(
                # if you want it editable, uncomment this line, and play around and see if you like it
                #self.overrideWidget.setEditable(1)
                # store a hash table of value->ComboBoxIndex
                # this is NOT the same as value->enumIndex!
                self.comboBoxIndexOfEnum = {}
                for i in range(0, self.overrideWidget.count()):
                    self.comboBoxIndexOfEnum[self.overrideWidget.itemText(i)] = i
        
    def data(self, column, role):
        if column != 2:
            return super(FieldItem, self).data(column, role)

        alert = Messaging.getAlert(self.msg, self.fieldInfo, self.index)
        if role == Qt.FontRole:
            font = QFont()
            if alert == 1:
                font.setBold(1)
            return font
        if role == Qt.ForegroundRole:
            brush = QBrush()
            if alert == 1:
                brush.setColor(Qt.red)
            return brush

        if role == Qt.DisplayRole:
            value  = str(Messaging.get(self.msg, self.fieldInfo, self.index))
            
            try:
                self.overrideWidget
                valueAsString = str(Messaging.get(self.msg, self.fieldInfo, self.index))
                
                if valueAsString in self.comboBoxIndexOfEnum:
                    #self.overrideWidget.setCurrentText(valueAsString)
                    self.overrideWidget.setCurrentIndex(self.comboBoxIndexOfEnum[valueAsString])
                else:
                    #self.overrideWidget.setEditText(valueAsString)
                    self.overrideWidget.setCurrentIndex(-1)
            except AttributeError:
                pass
                
            return str(value)
            
        return super(FieldItem, self).data(column, role)

    def overrideWidgetValueChanged(self, value):
        valueAsString = self.overrideWidget.itemText(value)
        # set the value in the message/header buffer
        Messaging.set(self.msg, self.fieldInfo, valueAsString)

        # no need to reset UI to value read from message, if user picked value from drop down.
        # \todo: need to if they type something, though.
        
    def setData(self, column, role, value):
        if not self.editable:
            return

        if not column == 2:
            return

        if self.fieldInfo.name == "ID":
            return
        
        if self.fieldInfo.type == "int" and value.startswith("0x"):
            value = str(int(value, 0))

        # if user deletes the value, for anything besides a string,
        # return without setting the new value
        if self.fieldInfo.type != "string" and value == "":
            return

        # set the value in the message/header buffer
        Messaging.set(self.msg, self.fieldInfo, value, self.index)

        # get the value back from the message/header buffer and pass on to super-class' setData
        super(FieldItem, self).setData(column, role, str(Messaging.get(self.msg, self.fieldInfo, self.index)))

# This is used for the bits within the containing bit
class FieldBits(FieldItem):
    def __init__(self, editable, tree_widget, msg, msg_key, bitfieldInfo, index):
       column_strings = [None, "    " + bitfieldInfo.name, "", bitfieldInfo.units, bitfieldInfo.description]
       super(FieldBits, self).__init__(editable, tree_widget, msg, msg_key, bitfieldInfo, column_strings=column_strings, index=index)

class FieldBitfieldItem(FieldItem):
    def __init__(self, editable, tree_widget, msg, msg_key, fieldInfo, index):
        super(FieldBitfieldItem, self).__init__(editable, tree_widget, msg, msg_key, fieldInfo, column_strings=[], index=index)

        for bitfieldInfo in fieldInfo.bitfieldInfo:
            bitfieldBitsItem = FieldBits(self.editable, tree_widget, self.msg, msg_key, bitfieldInfo, index)
            self.addChild(bitfieldBitsItem)
            if self.editable:
                try:
                    bitfieldBitsItem.overrideWidget
                    tree_widget.setItemWidget(bitfieldBitsItem, 2, bitfieldBitsItem.overrideWidget)
                except AttributeError:
                    pass

# This is for holding a list of elements of an array, each of which is a
# regular FieldItem or a FieldBitfieldItem.
class FieldArrayItem(QTreeWidgetItem):
    def __init__(self, editable, tree_widget, msg, msg_key, fieldInfo):
        column_strings = [None, fieldInfo.name, "", fieldInfo.units, fieldInfo.description]
        
        QTreeWidgetItem.__init__(self, None, column_strings)
        self.editable = editable

        self.fieldInfo = fieldInfo
        self.fieldName = fieldInfo.name
        self.msg = msg
        self.msg_key = msg_key

        for i in range(0, self.fieldInfo.count):
            if fieldInfo.bitfieldInfo == None:
                messageFieldTreeItem = FieldItem(self.editable, tree_widget, self.msg, self.msg_key, self.fieldInfo, [], i)
                self.addChild(messageFieldTreeItem)
            else:
                # This adds a bitfield container item, which in turn has bits within it.
                messageFieldTreeItem = FieldBitfieldItem(self.editable, tree_widget, self.msg, self.msg_key, fieldInfo, i)
                self.addChild(messageFieldTreeItem)

        if self.editable:
            self.setFlags(self.flags() | Qt.ItemIsEditable)

    def data(self, column, role):
        if column != 2:
            return super(FieldArrayItem, self).data(column, role)

        # There's no data to display for the array itself, all data is in children.
        if role == Qt.FontRole:
            return QFont()
        return ""

    def setData(self, column, role, value):
        # There's no data to set for the array, all data is in children.
        return

class QObjectProxy(QObject):
    send_message = pyqtSignal(object)
    def __init__(self):
        QObject.__init__(self)

class MessageItem(QTreeWidgetItem):
    def __init__(self, editable, tree_widget, msg, msg_key):
        QTreeWidgetItem.__init__(self, None, [msg.MsgName()])

        self.editable = editable
        
        self.qobjectProxy = QObjectProxy()

        self.tree_widget = tree_widget

        self.msg = msg
        self.msg_key = msg_key

        self.setup_fields(tree_widget)

        tree_widget.addTopLevelItem(self)
        tree_widget.resizeColumnToContents(0)
        self.setExpanded(True)

        # Create a timer to refresh at a fixed rate, so we don't refresh
        # needlessly fast for high rate data, and use too much CPU.
        # The timer isn't activated unless application code calls
        # set_msg_buffer().
        self.repaint_timer = QTimer()
        self.repaint_timer.setInterval(250)
        self.repaint_timer.timeout.connect(self.repaintAll)
        
        if self.editable:
            # text entry for rate, and a 'send' button
            self.sendTimer = QTimer()
            self.sendTimer.timeout.connect(lambda: self.qobjectProxy.send_message.emit(self.msg))
            containerWidget = QWidget(tree_widget)
            containerLayout = QHBoxLayout()
            containerWidget.setLayout(containerLayout)
            self.sendButton = QPushButton("Send", tree_widget)
            self.sendButton.autoFillBackground()
            self.sendButton.clicked.connect(self.sendClicked)
            self.rateEdit = QLineEdit("", tree_widget)
            self.rateEdit.setValidator(QDoubleValidator(0, 100, 2, containerWidget))
            self.rateEdit.setMaximumWidth(50)
            self.rateEdit.setFixedWidth(50)
            self.rateEdit.setPlaceholderText("Rate")
            containerLayout.addWidget(self.rateEdit)
            containerLayout.addWidget(QLabel("Hz"))
            containerLayout.addWidget(self.sendButton)
            tree_widget.setItemWidget(self, 4, containerWidget)
            
            for i in range(0, tree_widget.columnCount()):
                tree_widget.resizeColumnToContents(i);

    def repaintAll(self):
        # Refresh the paint on the entire tree
        # TODO This is not a good solution!  We should refresh *only* the item that changed, not whole tree!
        region = self.tree_widget.childrenRegion()
        self.tree_widget.setDirtyRegion(region)
        self.repaint_timer.stop()

    def set_msg_buffer(self, msg_buffer):
        self.msg.msg_buffer_wrapper["msg_buffer"] = msg_buffer
        self.msg.hdr.msg_buffer_wrapper["msg_buffer"] = msg_buffer
        if not self.repaint_timer.isActive():
            self.repaint_timer.start()
        #self.repaintAll()

    def setup_fields(self, tree_widget):
        headerTreeItemParent = QTreeWidgetItem(None, [ "Header" ])
        self.addChild(headerTreeItemParent)

        for headerFieldInfo in Messaging.hdr.fields:
            if headerFieldInfo.bitfieldInfo != None:
                headerFieldTreeItem = FieldBitfieldItem(self.editable, tree_widget, self.msg.hdr, None, headerFieldInfo, index=None)
            else:
                headerFieldTreeItem = FieldItem(self.editable, tree_widget, self.msg.hdr, None, headerFieldInfo, column_strings=[], index=None)
            headerTreeItemParent.addChild(headerFieldTreeItem)

        for fieldInfo in type(self.msg).fields:
            messageFieldTreeItem = None

            if fieldInfo.count == 1:
                if fieldInfo.bitfieldInfo != None:
                    messageFieldTreeItem = FieldBitfieldItem(self.editable, tree_widget, self.msg, self.msg_key, fieldInfo, index=None)
                else:
                    messageFieldTreeItem = FieldItem(self.editable, tree_widget, self.msg, self.msg_key, fieldInfo, column_strings=[], index=None)
            else:
                messageFieldTreeItem = FieldArrayItem(self.editable, tree_widget, self.msg, self.msg_key, fieldInfo)
            
            self.addChild(messageFieldTreeItem)
            try:
                messageFieldTreeItem.overrideWidget
                tree_widget.setItemWidget(messageFieldTreeItem, 2, messageFieldTreeItem.overrideWidget)
            except AttributeError:
                pass

    def sendClicked(self):
        if self.sendButton.text() == "Send":
            if self.rateEdit.text() == "" or self.rateEdit.text() == "0":
                self.qobjectProxy.send_message.emit(self.msg)
            else:
                self.sendButton.setText("Stop")
                rate = float(self.rateEdit.text())
                if rate > 0.01:
                    period = 1000.0/rate
                    # send once now, then periodically after
                    self.qobjectProxy.send_message.emit(self.msg)
                    self.sendTimer.start(period)
                else:
                    self.sendButton.text("Send")
        else:
            self.sendButton.setText("Send")
            self.sendTimer.stop()
