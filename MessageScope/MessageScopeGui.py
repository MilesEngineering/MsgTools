#!/usr/bin/env python3
import sys
import struct

from PySide.QtGui import *
from PySide.QtCore import *

sys.path.append("../MsgApp")
import MsgGui
from Messaging import Messaging

from TxMessageTreeWidgetItem import *

class MessageScopeGui(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "../obj/CodeGenerator/Python/", "Message Scope 0.1", argv, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.ConfigureGui(parent)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
        
        self.resize(800, 600)
        
        self.ReadTxDictionary()

    def ConfigureGui(self, parent):   
        hSplitter = QSplitter(parent);
        
        txSplitter = QSplitter(parent);
        rxSplitter = QSplitter(parent);

        txSplitter.setOrientation(Qt.Vertical)
        rxSplitter.setOrientation(Qt.Vertical)

        hSplitter.addWidget(txSplitter)
        hSplitter.addWidget(rxSplitter)
        
        self.txDictionary = QListWidget(parent);
        self.txDictionary.itemDoubleClicked.connect(self.onTxMessageSelected)

        self.rxDictionary = QListWidget(parent);

        self.txMsgs = QTreeWidget(parent);
        self.txMsgs.setColumnCount(4);
        
        txMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Send", "Description"]);
        
        self.txMsgs.setHeaderItem(txMsgsHeader);

        self.rxMessagesTabWidget = QTabWidget(self)

        txSplitter.addWidget(self.txDictionary);
        txSplitter.addWidget(self.txMsgs);
        rxSplitter.addWidget(self.rxDictionary);
        rxSplitter.addWidget(self.rxMessagesTabWidget);
        
        self.setCentralWidget(hSplitter)

    def ReadTxDictionary(self):
        print("Tx Dictionary:")
        for id in self.msgLib.MsgNameFromID:
            print(self.msgLib.MsgNameFromID[id], "=", id)
            newItem = QListWidgetItem()
            newItem.setText(self.msgLib.MsgNameFromID[id])
            self.txDictionary.addItem(newItem)

    def onTxMessageSelected(self, txListWidgetItem):
        messageName = txListWidgetItem.text()

        # Always add to TX panel even if the same message class may already exist
        # since we may want to send the same message with different contents/header/rates.
        messageTreeWidgetItem = TxMessageTreeWidgetItem(messageName, self.txMsgs, self.msgLib)
        messageTreeWidgetItem.send_message.connect(self.on_tx_message_send)

    def on_tx_message_send(self, messageBuffer):
        self.sendFn(messageBuffer.raw)

    def ProcessMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        msgId = hex(Messaging.hdr.GetID(msg))

        if not msgId in self.msgLib.MsgNameFromID:
            print("WARNING! No definition for ", msgId, "!\n")
            return

        msgName = self.msgLib.MsgNameFromID[msgId]
        msgClass = self.msgLib.MsgClassFromName[msgName]
        msgFields = msgClass.fields

        if(not(msgId in self.msgWidgets)):
            # create a new tree widget
            msgWidget = QTreeWidget()
            
            # add it to the tab widget, so the user can see it
            self.rxMessagesTabWidget.addTab(msgWidget, msgClass.__name__)
            
            # add headers, one for each message field
            header = []
            for field in msgFields:
                header.append(field["Name"])
            
            msgWidget.setHeaderLabels(header)

            count = 0
            for field in msgFields:
                msgWidget.resizeColumnToContents(count)
                count += 1
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[msgId] = msgWidget
        
        msgStringList = []

        for field in msgFields:                
            msgStringList.append(str(Messaging.get(msgClass, msg, field)))

        msgItem = QTreeWidgetItem(None, msgStringList)
        self.msgWidgets[msgId].addTopLevelItem(msgItem)


# main starts here
if __name__ == '__main__':
    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(sys.argv)
    msgScopeGui.show()
    sys.exit(app.exec_())
