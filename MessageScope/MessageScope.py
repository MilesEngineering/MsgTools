#!/usr/bin/env python3
import sys
import struct
import datetime

from PySide.QtGui import *
from PySide.QtCore import *

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui
from Messaging import Messaging

import TxTreeWidget

class MessageScopeGui(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Scope 0.1", argv, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.configure_gui(parent)
        
        self.resize(800, 600)
        
        self.ReadTxDictionary()

    def configure_gui(self, parent):   
        hSplitter = QSplitter(parent)
        
        txSplitter = QSplitter(parent)
        rxSplitter = QSplitter(parent)

        txSplitter.setOrientation(Qt.Vertical)
        rxSplitter.setOrientation(Qt.Vertical)

        hSplitter.addWidget(txSplitter)
        hSplitter.addWidget(rxSplitter)

        self.txDictionary = self.configure_tx_dictionary(parent)
        self.txMsgs = self.configure_tx_messages(parent)
        self.rx_message_list = self.configure_rx_message_list(parent)
        self.rx_messages_widget = self.configure_rx_messages_widget(parent)

        txSplitter.addWidget(self.txDictionary)
        txSplitter.addWidget(self.txMsgs)
        rxSplitter.addWidget(self.rx_message_list)
        rxSplitter.addWidget(self.rx_messages_widget)
        
        self.setCentralWidget(hSplitter)

    def configure_tx_dictionary(self, parent):
        txDictionary = QListWidget(parent)
        txDictionary.itemDoubleClicked.connect(self.onTxMessageSelected)
        return txDictionary

    def configure_tx_messages(self, parent):
        txMsgs = QTreeWidget(parent)
        txMsgs.setColumnCount(4)
        
        txMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        
        txMsgs.setHeaderItem(txMsgsHeader)
        return txMsgs

    def configure_rx_message_list(self, parent):
        self.rx_msg_list = {}
        rxMessageList = QListWidget(parent)
        return rxMessageList

    def configure_rx_messages_widget(self, parent):
        self.rx_msg_widgets = {}
        rxMessagesTreeWidget = QTreeWidget(parent)
        rxMessagesTreeWidget.setColumnCount(4)
        txMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        rxMessagesTreeWidget.setHeaderItem(txMsgsHeader)
        return rxMessagesTreeWidget

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
        message_class = self.msgLib.MsgClassFromName[messageName]
        messageBuffer = message_class.Create()

        messageTreeWidgetItem = TxTreeWidget.EditableMessageItem(messageName, self.txMsgs, message_class, messageBuffer)
        messageTreeWidgetItem.send_message.connect(self.on_tx_message_send)

    def on_tx_message_send(self, messageBuffer):
        self.sendFn(messageBuffer.raw)

    def ProcessMessage(self, msg_buffer):
        msg_id = hex(Messaging.hdr.GetID(msg_buffer))

        if not msg_id in self.msgLib.MsgNameFromID:
            print("WARNING! No definition for ", msg_id, "!\n")
            return

        msg_name = self.msgLib.MsgNameFromID[msg_id]
        msg_class = self.msgLib.MsgClassFromName[msg_name]
        msg_fields = msg_class.fields

        self.dsiplay_message_in_rx_list(msg_id, msg_name)
        self.display_message_in_rx_tree(msg_id, msg_name, msg_class, msg_buffer)

    def dsiplay_message_in_rx_list(self, msg_id, msg_name):
        if not msg_id in self.rx_msg_list:
            msg_list_item = QListWidgetItem(msg_name)

            self.rx_message_list.addItem(msg_list_item)
            self.rx_msg_list[msg_id] = msg_list_item

        self.rx_msg_list[msg_id].setText(msg_name + " (Last Received: " + str(datetime.datetime.now()) + ")")

    def display_message_in_rx_tree(self, msg_id, msg_name, msg_class, msg_buffer):
        if not msg_id in self.rx_msg_widgets:
            msg_widget = TxTreeWidget.MessageItem(msg_name, self.rx_messages_widget, msg_class, msg_buffer)
            self.rx_msg_widgets[msg_id] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)

        self.rx_msg_widgets[msg_id].set_msg_buffer(msg_buffer)

# main starts here
if __name__ == '__main__':
    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(sys.argv)
    msgScopeGui.show()
    sys.exit(app.exec_())
