#!/cygdrive/c/Python34/python.exe
import sys

from PySide.QtGui import *
from PySide.QtCore import *

from Messaging import Messaging
    
class TxMessageFieldTreeWidgetItem(QObject, QTreeWidgetItem):
    def __init__(self, messageClass, buffer, fieldInfo):
        columnStrings = [None, fieldInfo["Name"], "", fieldInfo["Units"], fieldInfo["Description"] ]

        QObject.__init__(self)
        QTreeWidgetItem.__init__(self, None, columnStrings)
        
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.fieldInfo = fieldInfo
        self.messageClass = messageClass
        self.buffer = buffer

    def data(self, column, role):
        if not column == 2:
            return super(TxMessageFieldTreeWidgetItem, self).data(column, role)

        value  = getattr(self.messageClass, self.fieldInfo["Get"])(self.buffer)
        return str(value)

    def setData(self, column, role, value):
        if not column == 2:
            return

        # set the value in the message/header buffer
        getattr(self.messageClass, self.fieldInfo["Set"])(self.buffer, value)

        # get the value back from the message/header buffer and pass on to super-class' setData
        super(TxMessageFieldTreeWidgetItem, self).setData(column, role, getattr(self.messageClass, self.fieldInfo["Get"])(self.buffer))

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

        for headerFieldInfo in Messaging.hdr.FIELDINFOS:
            headerFieldTreeItem = TxMessageFieldTreeWidgetItem(Messaging.hdr, self.messageBuffer, headerFieldInfo)
            headerTreeItemParent.addChild(headerFieldTreeItem)

        for fieldInfo in self.messageClass.FIELDINFOS:
            messageFieldTreeItem = TxMessageFieldTreeWidgetItem(self.messageClass, self.messageBuffer, fieldInfo)
            self.addChild(messageFieldTreeItem)

    def on_send_message_clicked(self):
        self.send_message.emit(self.messageBuffer)
