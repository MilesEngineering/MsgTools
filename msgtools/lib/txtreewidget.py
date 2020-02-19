#!/cygdrive/c/Python34/python.exe
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from msgtools.lib.messaging import Messaging

class FieldItem(QTreeWidgetItem):
    def __init__(self, msg, msg_key, fieldInfo, column_strings = []):
        column_strings = column_strings if len(column_strings) > 0 else [None, fieldInfo.name, "", fieldInfo.units, fieldInfo.description]
        
        QTreeWidgetItem.__init__(self, None, column_strings)
        
        self.fieldInfo = fieldInfo
        self.fieldName = fieldInfo.name
        self.msg = msg
        self.msg_key = msg_key
        
    def data(self, column, role):
        if column != 2:
            return super(FieldItem, self).data(column, role)

        alert = Messaging.getAlert(self.msg, self.fieldInfo)
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
            value  = Messaging.get(self.msg, self.fieldInfo)
            
            try:
                self.overrideWidget
                valueAsString = Messaging.get(self.msg, self.fieldInfo)
                
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

class EditableFieldItem(FieldItem):
    def __init__(self, msg, msg_key, fieldInfo, column_strings = []):
        super(EditableFieldItem, self).__init__(msg, msg_key, fieldInfo, column_strings)

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

    def overrideWidgetValueChanged(self, value):
        valueAsString = self.overrideWidget.itemText(value)
        # set the value in the message/header buffer
        Messaging.set(self.msg, self.fieldInfo, valueAsString)

        # no need to reset UI to value read from message, if user picked value from drop down.
        # \todo: need to if they type something, though.
        
    def setData(self, column, role, value):
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
        Messaging.set(self.msg, self.fieldInfo, value)

        # get the value back from the message/header buffer and pass on to super-class' setData
        super(FieldItem, self).setData(column, role, Messaging.get(self.msg, self.fieldInfo))

class FieldBits(FieldItem):
    def __init__(self, msg, msg_key, bitfieldInfo):
       column_strings = [None, "    " + bitfieldInfo.name, "", bitfieldInfo.units, bitfieldInfo.description]
       super(FieldBits, self).__init__(msg, msg_key, bitfieldInfo, column_strings)

class FieldBitfieldItem(FieldItem):
    def __init__(self, tree_widget, msg, msg_key, fieldInfo):
        super(FieldBitfieldItem, self).__init__(msg, msg_key, fieldInfo)

        for bitfieldInfo in fieldInfo.bitfieldInfo:
            bitfieldBitsItem = FieldBits(self.msg, msg_key, bitfieldInfo)
            self.addChild(bitfieldBitsItem)

class EditableFieldBits(EditableFieldItem):
    def __init__(self, msg, msg_key, bitfieldInfo):
       column_strings = [None, "    " + bitfieldInfo.name, "", bitfieldInfo.units, bitfieldInfo.description]
       super(EditableFieldBits, self).__init__(msg, msg_key, bitfieldInfo, column_strings)

class EditableFieldBitfieldItem(EditableFieldItem):
    def __init__(self, tree_widget, msg, msg_key, fieldInfo):
        super(EditableFieldBitfieldItem, self).__init__(msg, msg_key, fieldInfo)

        for bitfieldInfo in fieldInfo.bitfieldInfo:
            bitfieldBitsItem = EditableFieldBits(self.msg, msg_key, bitfieldInfo)
            self.addChild(bitfieldBitsItem)
            try:
                bitfieldBitsItem.overrideWidget
                tree_widget.setItemWidget(bitfieldBitsItem, 2, bitfieldBitsItem.overrideWidget)
            except AttributeError:
                pass

class FieldArrayItem(QTreeWidgetItem):
    def __init__(self, msg, msg_key, fieldInfo, field_array_constructor, index = None):
        column_strings = [None, fieldInfo.name, "", fieldInfo.units, fieldInfo.description]
        
        if index != None:
            column_strings[1] = "    [" + str(index) + "]"
        
        QTreeWidgetItem.__init__(self, None, column_strings)
        
        self.fieldInfo = fieldInfo
        if index == None:
            self.fieldName = fieldInfo.name
        else:
            self.fieldName = "%s[%d]" % (fieldInfo.name, index)
        self.msg = msg
        self.msg_key = msg_key
        self.index = index

        if index == None:
            for i in range(0, self.fieldInfo.count):
                messageFieldTreeItem = field_array_constructor(self.msg, self.msg_key, self.fieldInfo, field_array_constructor, i)
                self.addChild(messageFieldTreeItem)

    def data(self, column, role):
        if column != 2:
            return super(FieldArrayItem, self).data(column, role)

        if self.index == None:
            if role == Qt.FontRole:
                return QFont()
            return ""

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
            value  = Messaging.get(self.msg, self.fieldInfo, self.index)
            return str(value)

        return super(FieldArrayItem, self).data(column, role)

class EditableFieldArrayItem(FieldArrayItem):
    def __init__(self, msg, msg_key, fieldInfo, field_array_constructor, index = None):
        super(EditableFieldArrayItem, self).__init__(msg, msg_key, fieldInfo, field_array_constructor, index)

        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def setData(self, column, role, value):
        if self.index == None:
            return

        if column != 2:
            return

        if self.fieldInfo.name == "ID":
            return

        if self.fieldInfo.type == "int" and value.startswith("0x"):
            value = str(int(value, 0))

        # set the value in the message/header buffer
        Messaging.set(self.msg, self.fieldInfo, value, int(self.index))

        # get the value back from the message/header buffer and pass on to super-class' setData
        super(EditableFieldArrayItem, self).setData(column, role, Messaging.get(self.msg, self.fieldInfo, int(self.index)))

class QObjectProxy(QObject):
    send_message = pyqtSignal(object)
    def __init__(self):
        QObject.__init__(self)

class MessageItem(QTreeWidgetItem):
    def __init__(self, tree_widget, msg, msg_key,
                 child_constructor = FieldItem,
                 child_array_constructor = FieldArrayItem,
                 child_bitfield_constructor = FieldBitfieldItem):
        QTreeWidgetItem.__init__(self, None, [msg.MsgName()])
        
        self.qobjectProxy = QObjectProxy()

        self.tree_widget = tree_widget

        self.msg = msg
        self.msg_key = msg_key

        self.setup_fields(tree_widget, child_constructor, child_array_constructor, child_bitfield_constructor)

        tree_widget.addTopLevelItem(self)
        tree_widget.resizeColumnToContents(0)
        self.setExpanded(True)

    def repaintAll(self):
        # Refresh the paint on the entire tree
        # TODO This is not a good solution!  We should refresh *only* the item that changed, not whole tree!
        region = self.tree_widget.childrenRegion()
        self.tree_widget.setDirtyRegion(region)

    def set_msg_buffer(self, msg_buffer):
        self.msg.msg_buffer_wrapper["msg_buffer"] = msg_buffer
        self.msg.hdr.msg_buffer_wrapper["msg_buffer"] = msg_buffer
        self.repaintAll()

    def setup_fields(self, tree_widget, child_constructor, child_array_constructor, child_bitfield_constructor):
        headerTreeItemParent = QTreeWidgetItem(None, [ "Header" ])
        self.addChild(headerTreeItemParent)

        for headerFieldInfo in Messaging.hdr.fields:
            if headerFieldInfo.bitfieldInfo != None:
                headerFieldTreeItem = child_bitfield_constructor(tree_widget, self.msg.hdr, None, headerFieldInfo)
            else:
                headerFieldTreeItem = child_constructor(self.msg.hdr, None, headerFieldInfo)
            headerTreeItemParent.addChild(headerFieldTreeItem)

        for fieldInfo in type(self.msg).fields:
            messageFieldTreeItem = None

            if fieldInfo.count == 1:
                if fieldInfo.bitfieldInfo != None:
                    messageFieldTreeItem = child_bitfield_constructor(tree_widget, self.msg, self.msg_key, fieldInfo)
                else:
                    messageFieldTreeItem = child_constructor(self.msg, self.msg_key, fieldInfo)
            else:
                messageFieldTreeItem = child_array_constructor(self.msg, self.msg_key, fieldInfo, child_array_constructor)
            
            self.addChild(messageFieldTreeItem)
            try:
                messageFieldTreeItem.overrideWidget
                tree_widget.setItemWidget(messageFieldTreeItem, 2, messageFieldTreeItem.overrideWidget)
            except AttributeError:
                pass

class EditableMessageItem(MessageItem):

    def __init__(self, tree_widget, msg, msg_key):
        super(EditableMessageItem, self).__init__(tree_widget, msg, msg_key, EditableFieldItem, EditableFieldArrayItem, EditableFieldBitfieldItem)

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
