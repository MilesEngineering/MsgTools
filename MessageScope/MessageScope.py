#!/usr/bin/env python3
import sys
import struct
import datetime
import collections
import functools
import threading

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui
from Messaging import Messaging

import TxTreeWidget
plottingLoaded=0
try:
    from MsgPlot import MsgPlot
    plottingLoaded=1
except ImportError:
    print("Error loading plot interface.")
    print("Perhaps you forgot to install pyqtgraph.")

class RxRateCalculatorThread(QObject):
    rates_updated = pyqtSignal(object)

    def __init__(self, rx_msg_deque, thread_lock):
        super(RxRateCalculatorThread, self).__init__()

        self.rx_msg_deque = rx_msg_deque
        self.thread_lock = thread_lock

    @pyqtSlot()
    def run(self):
        rates = {}

        if self.thread_lock.acquire():
            for msg_key, rx_msg_deque in self.rx_msg_deque.items():
                rates[msg_key] = self.calculate_rate_for_msg(msg_key, rx_msg_deque)

            self.thread_lock.release()
            self.rates_updated.emit(rates)

    def calculate_rate_for_msg(self, msg_key, rx_msg_deque):
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
        MsgGui.MsgGui.__init__(self, "Message Scope 0.1", argv, [], parent)

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
        txDictionary.setHeaderLabels(["Transmit Dictionary"])
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

        rxMessageList.itemDoubleClicked.connect(self.onRxListDoubleClicked)
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
        for id in Messaging.MsgNameFromID:
            #print(Messaging.MsgNameFromID[id], "=", id)
            name = Messaging.MsgNameFromID[id]
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
            message_class = Messaging.MsgClassFromName[messageName]
            messageBuffer = message_class.Create()

            messageTreeWidgetItem = TxTreeWidget.EditableMessageItem(messageName, self.txMsgs, message_class, messageBuffer)
            messageTreeWidgetItem.qobjectProxy.send_message.connect(self.on_tx_message_send)

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
                    plotName = msg_class.MsgName() + "." + fieldInfo.name + "[" + str(fieldIndex) + "]"
                    print("adding plot of " + plotName)
                    if plottingLoaded:
                        msgPlot = MsgPlot(msg_class, fieldInfo, fieldIndex)
                        # add a tab for new plot
                        dock = QDockWidget(plotName, self)
                        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
                        #dock.setAllowedAreas()
                        dock.setWidget(msgPlot.plotWidget)
                        self.addDockWidget(Qt.RightDockWidgetArea, dock)
                        plotListForID.append(msgPlot)
        except AttributeError:
            print("caught exception AttributeError")
    
    def MsgRoute(self, msg_buffer):
        msg_route = []
        try:
            msg_route.append(str(Messaging.hdr.GetSource(msg_buffer)))
        except AttributeError:
            pass
        try:
            msg_route.append(str(Messaging.hdr.GetDestination(msg_buffer)))
        except AttributeError:
            pass
        try:
            msg_route.append(str(Messaging.hdr.GetDeviceID(msg_buffer)))
        except AttributeError:
            pass
        return msg_route

    def ProcessMessage(self, msg_buffer):
        msg_id = hex(Messaging.hdr.GetMessageID(msg_buffer))

        if not msg_id in Messaging.MsgNameFromID:
            print("WARNING! No definition for ", msg_id, "!\n")
            return

        msg_name = Messaging.MsgNameFromID[msg_id]
        msg_class = Messaging.MsgClassFromName[msg_name]
        msg_fields = msg_class.fields

        msg_key = ",".join(self.MsgRoute(msg_buffer)) + "," + msg_id
        
        self.display_message_in_rx_list(msg_key, msg_name, msg_buffer)
        self.display_message_in_rx_tree(msg_key, msg_name, msg_class, msg_buffer)
        self.display_message_in_plots(msg_class, msg_buffer)

    def onRxListDoubleClicked(self, rxListItem):
        msg_key = rxListItem.msg_key
        msg_name = rxListItem.msg_name
        msg_buffer = rxListItem.msg_buffer
        msg_class = Messaging.MsgClassFromName[msg_name]
        self.add_message_to_rx_tree(msg_key, msg_name, msg_class, msg_buffer)

    def display_message_in_rx_list(self, msg_key, msg_name, msg_buffer):
        rx_time = datetime.datetime.now()

        if not msg_key in self.rx_msg_list:
            widget_name = msg_name
            msg_route = self.MsgRoute(msg_buffer)
            if len(msg_route) > 0 and not(all ("0" == a for a in msg_route)):
                widget_name += " ("+"->".join(msg_route)+")"
            msg_list_item = QTreeWidgetItem([ widget_name, str(rx_time), "- Hz" ])
            msg_list_item.msg_key = msg_key
            msg_list_item.msg_name = msg_name

            self.rx_message_list.addTopLevelItem(msg_list_item)
            self.rx_message_list.resizeColumnToContents(0)
            self.rx_msg_list[msg_key] = msg_list_item

            # Initialize a Deque with an empty iterable with a maxlen of 10
            if self.thread_lock.acquire():
                self.rx_msg_list_timestamps[msg_key] = collections.deque([], 10)
                self.thread_lock.release()

        if self.thread_lock.acquire():
            self.rx_msg_list_timestamps[msg_key].appendleft(rx_time)
            self.thread_lock.release()

        self.rx_msg_list[msg_key].setText(1, str(rx_time))
        self.rx_msg_list[msg_key].msg_buffer = msg_buffer

    def show_rx_msg_rates(self, rx_rates):
        for msg_key, rate in rx_rates.items():
            rate = rx_rates[msg_key]
            output = ""

            if rate is None:
                output = "-- Hz"
            else:
                output = "{0:0.1f} Hz".format(rate)

            self.rx_msg_list[msg_key].setText(2, output)

    def add_message_to_rx_tree(self, msg_key, msg_name, msg_class, msg_buffer):
        if not msg_key in self.rx_msg_widgets:
            msg_widget = TxTreeWidget.MessageItem(msg_name, self.rx_messages_widget, msg_class, msg_buffer)
            self.rx_msg_widgets[msg_key] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)
            self.rx_messages_widget.resizeColumnToContents(0)

    def display_message_in_rx_tree(self, msg_key, msg_name, msg_class, msg_buffer):
        if msg_key in self.rx_msg_widgets:
            self.rx_msg_widgets[msg_key].set_msg_buffer(msg_buffer)
    
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
