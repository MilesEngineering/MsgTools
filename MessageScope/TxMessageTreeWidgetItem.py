#!/cygdrive/c/Python34/python.exe
import sys

from PySide.QtGui import *
from PySide.QtCore import *

class TxMessageFieldTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, messageClass, messageObject, fieldInfo):
        columnStrings = [None, fieldInfo["Name"], "", fieldInfo["Units"], fieldInfo["Description"] ]
        super(TxMessageFieldTreeWidgetItem, self).__init__(None, columnStrings)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.fieldInfo = fieldInfo
        self.messageClass = messageClass
        self.messageObject = messageObject

    def setData(self, column, role, value):
        if not column == 2:
            return

        getattr(self.messageClass, self.fieldInfo["Set"])(self.messageObject, value)

        super(TxMessageFieldTreeWidgetItem, self).setData(column, role, getattr(self.messageClass, self.fieldInfo["Get"])(self.messageObject))

class TxMessageTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, messageName, treeWidget, msgLib):
        super(TxMessageTreeWidgetItem, self).__init__(None, [messageName])
        self.messageClass = msgLib.MsgClassFromName[messageName]
        self.messageObject = self.messageClass.Create()

        self.setupFields(treeWidget)

        treeWidget.addTopLevelItem(self)

        sendButton = QPushButton("Send", treeWidget)
        sendButton.autoFillBackground()
        sendButton.clicked.connect(self.onSendMessageClicked)
        treeWidget.setItemWidget(self, 4, sendButton)

    def setupFields(self, treeWidget):
        for fieldInfo in self.messageClass.FIELDINFOS:
            messageFieldTreeItem = TxMessageFieldTreeWidgetItem(self.messageClass, self.messageObject, fieldInfo);
            
            self.addChild(messageFieldTreeItem);
            treeWidget.itemChanged.connect(self.onTxMsgChildItemChanged)

    def onTxMsgChildItemChanged(self, item, column):
        if(column != 2):
            return

        if(not item is self):
            return

        newValue = item.text(column)
        print(newValue)

    def onSendMessageClicked(self):
        print("Send message")
