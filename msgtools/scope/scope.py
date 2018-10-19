#!/usr/bin/env python3
import sys
import struct
from datetime import datetime
import collections
import functools
import threading
import argparse

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui
import msgtools.lib.msgcsv as msgcsv
import msgtools.debug.debug

import msgtools.lib.txtreewidget as txtreewidget
plottingLoaded=0
try:
    from msgtools.lib.msgplot import MsgPlot
    plottingLoaded=1
except ImportError as e:
    print("Error loading plot interface ["+str(e)+"]")
    print("Perhaps you forgot to install pyqtgraph.")
except RuntimeError as e:
    print("Error loading plot interface ["+str(e)+"]")
    print("Perhaps you need to install the PyQt5 version of pyqtgraph.")
    
DESCRIPTION='''MsgScope provides a graphical interface that allow syou to view, plot, and send
    messages.  It requires defined messages in Python.  A list of discovered messages will be
    displayed in the upper left of the UI.'''

class RxRateCalculatorThread(QObject):
    rates_updated = pyqtSignal(object)

    def __init__(self, rx_msg_deque, thread_lock):
        super(RxRateCalculatorThread, self).__init__()

        self.rx_msg_deque = rx_msg_deque
        self.thread_lock = thread_lock

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
        if(average_time_delta == 0):
            average_time_delta = 1
        average_rate = 1 / average_time_delta

        rx_msg_deque.pop()

        return average_rate


def slim_vbox(a, b):
    vLayout = QVBoxLayout()
    vLayout.setSpacing(0)
    vLayout.setContentsMargins(0,0,0,0)
    vLayout.addWidget(a)
    vLayout.addWidget(b)

    vBox = QWidget()
    vBox.setLayout(vLayout)
    return vBox

def vsplitter(parent, *argv):
    splitter = QSplitter(parent)
    splitter.setOrientation(Qt.Vertical)
    for arg in argv:
        splitter.addWidget(arg)
    return splitter

class ClosableDockWidget(QDockWidget):
    def __init__(self, name, parent, widget, itemList):
        super(QDockWidget,self).__init__(name, parent)
        self.setObjectName(name)
        self.setWidget(widget)
        # list it needs to be removed from
        self.itemList = itemList

    def closeEvent(self, ev):
        self.itemList.remove(self.widget())
        self.parent().removeDockWidget(self)

class MessageScopeGui(msgtools.lib.gui.Gui):
    def __init__(self, args, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Message Scope 0.1", args, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.configure_gui(parent)
        
        self.ReadTxDictionary()

    def configure_gui(self, parent):
        # create widgets for tx
        self.txDictionary = self.configure_tx_dictionary(parent)
        self.txMsgs = self.configure_tx_messages(parent)
        txClearBtn = QPushButton("Clear")
        self.debugWidget = msgtools.debug.debug.MsgDebugWidget([], parent)
        self.debugWidget.messageOutput.connect(self.SendMsg)
        # tracking what reply to expect
        self.expectedReply = None
        
        # add them to the tx layout
        txVBox = slim_vbox(self.txMsgs, txClearBtn)
        self.txSplitter = vsplitter(parent, self.txDictionary, txVBox, self.debugWidget)
        
        # create widgets for rx
        self.rx_message_list = self.configure_rx_message_list(parent)
        self.rx_messages_widget = self.configure_rx_messages_widget(parent)
        self.configure_msg_plots(parent)
        rxClearListBtn = QPushButton("Clear")
        rxClearMsgsBtn = QPushButton("Clear")
        
        # add them to the rx layout
        rxMsgListBox = slim_vbox(self.rx_message_list, rxClearListBtn)
        rxMsgsBox = slim_vbox(self.rx_messages_widget, rxClearMsgsBtn)
        self.rxSplitter = vsplitter(parent, rxMsgListBox, rxMsgsBox)

        # top level horizontal splitter to divide the screen
        self.hSplitter = QSplitter(parent)
        self.hSplitter.addWidget(self.txSplitter)
        self.hSplitter.addWidget(self.rxSplitter)

        self.setCentralWidget(self.hSplitter)
    
        # connect signals for 'clear' buttons
        txClearBtn.clicked.connect(self.clear_tx)
        rxClearListBtn.clicked.connect(self.clear_rx_list)
        rxClearMsgsBtn.clicked.connect(self.clear_rx_msgs)
        
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
        rxMessagesTreeWidget.setDragEnabled(1)
        rxMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        rxMessagesTreeWidget.setHeaderItem(rxMsgsHeader)
        rxMessagesTreeWidget.itemDoubleClicked.connect(self.onRxMessageFieldSelected)
        return rxMessagesTreeWidget

    def ReadTxDictionary(self):
        #print("Tx Dictionary:")
        for id in Messaging.MsgNameFromID:
            name = Messaging.MsgNameFromID[id]
            components = name.split('.')
            dirs = components[:-1]
            msgName = components[-1]
            
            parentWidget = self.txDictionary
            parentPath = ""
            for dir in dirs:
                # find the node that matches the directory we're looking for
                dirItemMatches = self.txDictionary.findItems(dir, Qt.MatchExactly | Qt.MatchRecursive, 0)
                foundMatch = False
                for dirItem in dirItemMatches:
                    try:
                        if parentPath == dirItem.parentPath:
                            parentWidget = dirItem
                            foundMatch = True
                            break
                    except AttributeError:
                        pass
                # if we didn't find the node for the directory, add it
                if not foundMatch:
                    newWidget = QTreeWidgetItem(parentWidget)
                    newWidget.setText(0, dir)
                    newWidget.parentPath = parentPath
                    parentWidget = newWidget
                parentPath += dir + "."
            msgItem = QTreeWidgetItem(parentWidget)
            msgItem.setText(0, msgName)
            msgItem.msgName = name
        self.txDictionary.sortByColumn(0, Qt.AscendingOrder)

    def onTxMessageSelected(self, txListWidgetItem):
        # directories have children but messages don't, so only add messages by verifying the childCount is zero
        if txListWidgetItem.childCount() == 0:
            messageName = txListWidgetItem.msgName
            # Always add to TX panel even if the same message class may already exist
            # since we may want to send the same message with different contents/header/rates.
            message_class = Messaging.MsgClassFromName[messageName]
            messageObj = message_class() # invoke constructor

            messageTreeWidgetItem = txtreewidget.EditableMessageItem(self.txMsgs, messageObj)
            messageTreeWidgetItem.qobjectProxy.send_message.connect(self.on_tx_message_send)

    def on_open(self):
        plots = self.settings.value("plotList", "")
        if plots:
            plotList = plots.split("|")
            for plot in plotList:
                msg_key = plot.split(":")[0]
                msg_id = msg_key.split(',')[-1]
                try:
                    msgName = Messaging.MsgNameFromID[msg_id]
                except KeyError:
                    print('Error!  msg_id ' + msg_id + ' is undefined!')
                    continue
                msgClass = Messaging.MsgClassFromName[msgName]
                
                fieldNames = plot.split(":")[1].split(",")
                msgPlot = None
                for fieldName in fieldNames:
                    try:
                        if msgPlot == None:
                            msgPlot = self.addPlot(msg_key, msgClass, fieldName)
                        else:
                            msgPlot.addLine(msgClass, fieldName)
                    except MsgPlot.PlotError as e:
                        print(e)
        self.txSplitter.restoreState(self.settings.value("txSplitterSizes", self.txSplitter.saveState()));
        self.rxSplitter.restoreState(self.settings.value("rxSplitterSizes", self.rxSplitter.saveState()));
        self.hSplitter.restoreState(self.settings.value("hSplitterSizes", self.hSplitter.saveState()));
        self.debugWidget.textEntryWidget.restoreState(self.settings.value("cmdHistory", self.debugWidget.textEntryWidget.saveState()));

    def on_close(self):
        plotList = ""
        for msg_key in self.msgPlots:
            plotListForID = self.msgPlots[msg_key]
            for plot in plotListForID:
                plotConfig = msg_key + ":"
                for line in plot.lines:
                    plotConfig += "%s[%d]," % (line.fieldInfo.name, line.fieldSubindex)
                plotConfig = plotConfig[:-1]
                plotList += plotConfig + "|"
        if plotList:
            plotList = plotList[:-1]
        self.settings.setValue("plotList", plotList)
        
        # save splitter sizes and command history
        self.settings.setValue("txSplitterSizes", self.txSplitter.saveState());
        self.settings.setValue("rxSplitterSizes", self.rxSplitter.saveState());
        self.settings.setValue("hSplitterSizes",  self.hSplitter.saveState());
        self.settings.setValue("cmdHistory", self.debugWidget.textEntryWidget.saveState());
            
    def on_tx_message_send(self, msg):
        if not self.connected:
            self.OpenConnection()
        text = msg.MsgName() + " " + msgcsv.toCsv(msg)
        self.debugWidget.textEntryWidget.addText(text + " -> Msg\n> ")
        self.debugWidget.textEntryWidget.addToHistory(text)
        self.SendMsg(msg)
    
    def addPlot(self, msg_key, msgClass, fieldName):
        plotListForID = []
        if msg_key in self.msgPlots:
            plotListForID = self.msgPlots[msg_key]
        else:
            self.msgPlots[msg_key] = plotListForID
        plotName = msgClass.MsgName()
        if plottingLoaded:
            msgPlot = MsgPlot(msgClass, fieldName)
            # add a dock widget for new plot
            dockWidget = ClosableDockWidget(plotName, self, msgPlot, plotListForID)
            self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
            # Change title when plot is paused/resumed
            msgPlot.Paused.connect(lambda paused: dockWidget.setWindowTitle(plotName+" (PAUSED)" if paused else plotName))
            msgPlot.AddLineError.connect(lambda s: QMessageBox.warning(self, "Message Scope", s))
            plotListForID.append(msgPlot)
            return msgPlot
        
    def onRxMessageFieldSelected(self, rxWidgetItem):
        if isinstance(rxWidgetItem, txtreewidget.FieldItem) or isinstance(rxWidgetItem, txtreewidget.FieldArrayItem):
            fieldInfo = rxWidgetItem.fieldInfo
            msg_id = hex(rxWidgetItem.msg.hdr.GetMessageID())
            msg_key = ",".join(Messaging.MsgRoute(rxWidgetItem.msg)) + "," + msg_id
            try:
                msgPlot = self.addPlot(msg_key, type(rxWidgetItem.msg), rxWidgetItem.fieldName)
                if msgPlot:
                    msgPlot.addData(rxWidgetItem.msg)
            except MsgPlot.PlotError as e:
                QMessageBox.warning(self, "Message Scope", str(e))
                
    def ProcessMessage(self, msg):
        self.debugWidget.ProcessMessage(msg)

        hdr = msg.hdr
        msg_id = hex(hdr.GetMessageID())

        msg_key = ",".join(Messaging.MsgRoute(msg)) + "," + msg_id
        
        self.display_message_in_rx_list(msg_key, msg)
        self.display_message_in_rx_tree(msg_key, msg)
        self.display_message_in_plots(msg_key, msg)

    def onRxListDoubleClicked(self, rxListItem):
        self.add_message_to_rx_tree(rxListItem.msg_key, rxListItem.msg)

    def display_message_in_rx_list(self, msg_key, msg):
        rx_time = datetime.now()

        if not msg_key in self.rx_msg_list:
            widget_name = msg.MsgName()
            msg_route = Messaging.MsgRoute(msg)
            if len(msg_route) > 0 and not(all ("0" == a for a in msg_route)):
                widget_name += " ("+",".join(msg_route)+")"
            msg_list_item = QTreeWidgetItem([ widget_name, rx_time.strftime('%H:%M:%S.%f')[:-3], "- Hz" ])
            msg_list_item.msg_key = msg_key
            msg_list_item.msg = msg

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

        self.rx_msg_list[msg_key].setText(1, rx_time.strftime('%H:%M:%S.%f')[:-3])
        self.rx_msg_list[msg_key].msg = msg

    def show_rx_msg_rates(self, rx_rates):
        for msg_key, rate in rx_rates.items():
            rate = rx_rates[msg_key]
            output = ""

            if rate is None:
                output = "-- Hz"
            else:
                output = "{0:0.1f} Hz".format(rate)

            try:
                self.rx_msg_list[msg_key].setText(2, output)
            except KeyError:
                # ignore errors relates to the item disappearing from the rx_msg_list.
                # these are caused by the list getting cleared
                pass

    def add_message_to_rx_tree(self, msg_key, msg):
        if not msg_key in self.rx_msg_widgets:
            msg_widget = txtreewidget.MessageItem(self.rx_messages_widget, msg)
            self.rx_msg_widgets[msg_key] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)
            self.rx_messages_widget.resizeColumnToContents(0)

    def display_message_in_rx_tree(self, msg_key, msg):
        if msg_key in self.rx_msg_widgets:
            self.rx_msg_widgets[msg_key].set_msg_buffer(msg.rawBuffer())
    
    def display_message_in_plots(self, msg_key, msg):
        if msg_key in self.msgPlots:
            plotListForID = self.msgPlots[msg_key]
            for plot in plotListForID:
                plot.addData(msg)
    
    def clear_rx_list(self):
        if self.thread_lock.acquire():
            self.rx_msg_list = {}
            self.rx_msg_list_timestamps = {}
            self.rx_message_list.clear()
            self.thread_lock.release()

    def clear_rx_msgs(self):
        self.rx_msg_widgets = {}
        self.rx_messages_widget.clear()

    def clear_tx(self):
        self.txMsgs.clear()

def main():
    # Setup a command line processor...
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(args)
    msgScopeGui.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
