#!/cygdrive/c/Python34/python.exe
import sys

from PySide.QtGui import *
from PySide.QtCore import *

from Messaging import Messaging
    
class TxMessageFieldTreeWidgetItem(QObject, QTreeWidgetItem):
    def __init__(self, messageClass, buffer, fieldInfo, index=0):
        QObject.__init__(self)

        columnStrings = [None, fieldInfo.name, "", fieldInfo.units, fieldInfo.description]
        if(fieldInfo.count != 1):
            columnStrings[1] += "[" + str(index) + "]"
        QTreeWidgetItem.__init__(self, None, columnStrings)
        
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.fieldInfo = fieldInfo
        self.messageClass = messageClass
        self.buffer = buffer
        self.index = index

    def data(self, column, role):
        if not column == 2:
            return super(TxMessageFieldTreeWidgetItem, self).data(column, role)

        if not role == Qt.DisplayRole:
            return None

        value  = self.messageClass.get(self.buffer, self.fieldInfo)
        return str(value)

    def setData(self, column, role, value):
        if not column == 2:
            return

        if self.fieldInfo.name == "ID":
            return

        # set the value in the message/header buffer
        self.messageClass.set(self.buffer, self.fieldInfo, value, self.index)

        # get the value back from the message/header buffer and pass on to super-class' setData
        super(TxMessageFieldTreeWidgetItem, self).setData(column, role, self.messageClass.get(self.buffer, self.fieldInfo, self.index))

class TxMessageTreeWidgetItem(QObject, QTreeWidgetItem):
    send_message = Signal(object)

    def __init__(self, messageName, treeWidget, msgLib):
        QObject.__init__(self)
        QTreeWidgetItem.__init__(self, None, [messageName])

        self.messageClass = msgLib.MsgClassFromName[messageName]
        self.messageBuffer = self.messageClass.Create()

        self.setup_fields(treeWidget)

        treeWidget.addTopLevelItem(self)

        sendButton = QPushButton("Send", treeWidget)
        sendButton.autoFillBackground()
        sendButton.clicked.connect(self.on_send_message_clicked)
        treeWidget.setItemWidget(self, 4, sendButton)

    def setup_fields(self, treeWidget):
        headerTreeItemParent = QTreeWidgetItem(None, [ "Header" ])
        self.addChild(headerTreeItemParent)

        for headerFieldInfo in Messaging.hdr.fields:
            headerFieldTreeItem = TxMessageFieldTreeWidgetItem(Messaging.hdr, self.messageBuffer, headerFieldInfo)
            headerTreeItemParent.addChild(headerFieldTreeItem)

        for fieldInfo in self.messageClass.fields:
            if(fieldInfo.count == 1):
                messageFieldTreeItem = TxMessageFieldTreeWidgetItem(self.messageClass, self.messageBuffer, fieldInfo)
                self.addChild(messageFieldTreeItem)
            else:
                for i in range(0,fieldInfo.count):
                    messageFieldTreeItem = TxMessageFieldTreeWidgetItem(self.messageClass, self.messageBuffer, fieldInfo, i)
                    self.addChild(messageFieldTreeItem)
    def on_send_message_clicked(self):
        self.send_message.emit(self.messageBuffer)
