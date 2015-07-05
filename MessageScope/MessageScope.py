#!/usr/bin/env python3
import sys
import struct
import datetime
import collections
import functools
import threading

from PySide.QtGui import *
from PySide.QtCore import *

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui
from Messaging import Messaging

import TxTreeWidget
from MsgPlot import MsgPlot


class RxRateCalculatorThread(QObject):
    rates_updated = Signal(object)

    def __init__(self, rx_msg_deque, thread_lock):
        super(RxRateCalculatorThread, self).__init__()

        self.rx_msg_deque = rx_msg_deque
        self.thread_lock = thread_lock

    @Slot()
    def run(self):
        rates = {}

        if self.thread_lock.acquire():
            for msg_id, rx_msg_deque in self.rx_msg_deque.items():
                rates[msg_id] = self.calculate_rate_for_msg(msg_id, rx_msg_deque)

            self.thread_lock.release()
            self.rates_updated.emit(rates)

    def calculate_rate_for_msg(self, msg_id, rx_msg_deque):
        if len(rx_msg_deque) <= 1:
            return None

        deltas = []
        for i in range(0, len(rx_msg_deque) - 1):
            deltas.append((rx_msg_deque[i] - rx_msg_deque[i + 1]).total_seconds())
        
        average_time_delta = sum(deltas) / float(len(deltas))
        average_rate = 1 / average_time_delta

        rx_msg_deque.pop()

        return average_rate


class MessageScopeGui(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Scope 0.1", argv, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.configure_gui(parent)
        
        self.resize(1000, 600)
        
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
        self.configure_msg_plots(parent)

        txSplitter.addWidget(self.txDictionary)
        txSplitter.addWidget(self.txMsgs)
        rxSplitter.addWidget(self.rx_message_list)
        rxSplitter.addWidget(self.rx_messages_widget)
        
        self.setCentralWidget(hSplitter)
    
    def configure_msg_plots(self, parent):
        self.msgPlots = {}

    def configure_tx_dictionary(self, parent):
        txDictionary = QTreeWidget(parent)
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
        self.rx_msg_list_timestamps = {}
        
        self.thread_lock = threading.Lock()
        rx_rate_calculator = RxRateCalculatorThread(self.rx_msg_list_timestamps, self.thread_lock)
        rx_rate_calculator.rates_updated.connect(self.show_rx_msg_rates)
        timer = QTimer(self)

        # TODO: Why do I have to use a lambda? connecting directly to the run slot does not seem to work
        timer.timeout.connect(lambda: rx_rate_calculator.run())
        timer.start(1000)

        rxMessageList = QTreeWidget(parent)
        rxMessageList.setColumnCount(3)
        rxMsgHeader = QTreeWidgetItem(None, [ "Name", "Last Received", "Rx Rate" ])
        rxMessageList.setHeaderItem(rxMsgHeader)
        return rxMessageList

    def configure_rx_messages_widget(self, parent):
        self.rx_msg_widgets = {}
        rxMessagesTreeWidget = QTreeWidget(parent)
        rxMessagesTreeWidget.setColumnCount(4)
        rxMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        rxMessagesTreeWidget.setHeaderItem(rxMsgsHeader)
        rxMessagesTreeWidget.itemDoubleClicked.connect(self.onRxMessageFieldSelected)
        return rxMessagesTreeWidget

    def ReadTxDictionary(self):
        print("Tx Dictionary:")
        for id in self.msgLib.MsgNameFromID:
            #print(self.msgLib.MsgNameFromID[id], "=", id)
            name = self.msgLib.MsgNameFromID[id]
            (msgDir, msgName) = name.split('.')
            addFn = None
            
            parentWidget = None
            if msgDir == None:
                parentWidget = self.txDictionary
            else:
                dirItemMatches = self.txDictionary.findItems(msgDir, Qt.MatchExactly, 0)
                if(len(dirItemMatches) > 0):
                    parentWidget = dirItemMatches[0]
                else:
                    parentWidget = QTreeWidgetItem(self.txDictionary)
                    parentWidget.setText(0, msgDir)
            msgItem = QTreeWidgetItem(parentWidget)
            msgItem.setText(0, msgName)
        self.txDictionary.sortByColumn(0, Qt.AscendingOrder)

    def onTxMessageSelected(self, txListWidgetItem):
        parentWidget = txListWidgetItem.parent()
        messageName = "." + txListWidgetItem.text(0)
        if not parentWidget is None:
            messageName = parentWidget.text(0) + messageName

        # directories have children but messages don't, so only add messages by verifying the childCount is zero
        if txListWidgetItem.childCount() == 0:
            # Always add to TX panel even if the same message class may already exist
            # since we may want to send the same message with different contents/header/rates.
            message_class = self.msgLib.MsgClassFromName[messageName]
            messageBuffer = message_class.Create()

            messageTreeWidgetItem = TxTreeWidget.EditableMessageItem(messageName, self.txMsgs, message_class, messageBuffer)
            messageTreeWidgetItem.send_message.connect(self.on_tx_message_send)

    def on_tx_message_send(self, messageBuffer):
        self.sendFn(messageBuffer.raw)
    
    def onRxMessageFieldSelected(self, rxWidgetItem):
        try:
            if isinstance(rxWidgetItem, TxTreeWidget.FieldItem) or isinstance(rxWidgetItem, TxTreeWidget.FieldArrayItem):
                fieldInfo = rxWidgetItem.fieldInfo
                fieldIndex = 0
                if isinstance(rxWidgetItem, TxTreeWidget.FieldArrayItem):
                    fieldIndex = rxWidgetItem.index
                msg_class = rxWidgetItem.msg_class
                plotListForID = []
                if msg_class.ID in self.msgPlots:
                    plotListForID = self.msgPlots[msg_class.ID]
                else:
                    self.msgPlots[msg_class.ID] = plotListForID
                alreadyThere = False
                for plot in plotListForID:
                    if plot.fieldInfo == fieldInfo and plot.fieldSubindex == fieldIndex:
                        alreadyThere = True
                if not alreadyThere:
                    print("adding plot of " + msg_class.MsgName() + "." + fieldInfo.name + "[" + str(fieldIndex) + "]")
                    msgPlot = MsgPlot(msg_class, fieldInfo, fieldIndex)
                    plotListForID.append(msgPlot)
        except AttributeError:
            print("caught exception AttributeError")

    def ProcessMessage(self, msg_buffer):
        msg_id = hex(Messaging.hdr.GetID(msg_buffer))

        if not msg_id in self.msgLib.MsgNameFromID:
            print("WARNING! No definition for ", msg_id, "!\n")
            return

        msg_name = self.msgLib.MsgNameFromID[msg_id]
        msg_class = self.msgLib.MsgClassFromName[msg_name]
        msg_fields = msg_class.fields

        self.display_message_in_rx_list(msg_id, msg_name)
        self.display_message_in_rx_tree(msg_id, msg_name, msg_class, msg_buffer)
        self.display_message_in_plots(msg_class, msg_buffer)

    def display_message_in_rx_list(self, msg_id, msg_name):
        rx_time = datetime.datetime.now()

        if not msg_id in self.rx_msg_list:
            msg_list_item = QTreeWidgetItem([ msg_name, str(rx_time), "- Hz" ])

            self.rx_message_list.addTopLevelItem(msg_list_item)
            self.rx_msg_list[msg_id] = msg_list_item

            # Initialize a Deque with an empty iterable with a maxlen of 10
            if self.thread_lock.acquire():
                self.rx_msg_list_timestamps[msg_id] = collections.deque([], 10)
                self.thread_lock.release()

        if self.thread_lock.acquire():
            self.rx_msg_list_timestamps[msg_id].appendleft(rx_time)
            self.thread_lock.release()

        self.rx_msg_list[msg_id].setText(1, str(rx_time))

    def show_rx_msg_rates(self, rx_rates):
        for msg_id, rate in rx_rates.items():
            rate = rx_rates[msg_id]
            output = ""

            if rate is None:
                output = "-- Hz"
            else:
                output = "{0:0.1f} Hz".format(rate)

            self.rx_msg_list[msg_id].setText(2, output)

    def display_message_in_rx_tree(self, msg_id, msg_name, msg_class, msg_buffer):
        if not msg_id in self.rx_msg_widgets:
            msg_widget = TxTreeWidget.MessageItem(msg_name, self.rx_messages_widget, msg_class, msg_buffer)
            self.rx_msg_widgets[msg_id] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)

        self.rx_msg_widgets[msg_id].set_msg_buffer(msg_buffer)
    
    def display_message_in_plots(self, msg_class, msg_buffer):
        #print("checking for plots of " + str(msg_class.ID))
        if msg_class.ID in self.msgPlots:
            #print("found list of plots for " + str(msg_class.ID))
            plotListForID = self.msgPlots[msg_class.ID]
            for plot in plotListForID:
                #print("found plot of " + msg_class.MsgName() + "." + plot.fieldInfo.name + "[" + str(plot.fieldSubindex) + "]")
                plot.addData(msg_buffer)

# main starts here
if __name__ == '__main__':
    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(sys.argv)
    msgScopeGui.show()
    sys.exit(app.exec_())
