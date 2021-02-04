#!/usr/bin/env python3
import os
import sys
import struct
from datetime import datetime
import collections
import functools
import argparse

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
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

def slim_vbox(a, b, c=None):
    vLayout = QVBoxLayout()
    vLayout.setSpacing(0)
    vLayout.setContentsMargins(0,0,0,0)
    vLayout.addWidget(a)
    if c == None:
        vLayout.addWidget(b)
    else:
        hLayout = QHBoxLayout()
        hLayout.setSpacing(0)
        hLayout.setContentsMargins(0,0,0,0)
        hLayout.addWidget(b)
        hLayout.addWidget(c)
        vLayout.addLayout(hLayout)

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
    def __init__(self, name, parent, widget, itemList, itemList2):
        super(QDockWidget,self).__init__(name, parent)
        self.setObjectName(name)
        self.setWidget(widget)
        # list it needs to be removed from
        self.itemList = itemList
        self.itemList2 = itemList2

    def closeEvent(self, ev):
        self.itemList.remove(self.widget())
        self.itemList2.remove(self.widget())
        self.parent().removeDockWidget(self)

class MessageScopeGui(msgtools.lib.gui.Gui):
    def __init__(self, args, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Message Scope 0.1", args, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.configure_gui(parent, args.debugdicts)
        
        self.ReadTxDictionary()

    def configure_gui(self, parent, debugdicts):
        # create widgets for tx
        self.txDictionary = self.configure_tx_dictionary(parent)
        self.txMsgs = self.configure_tx_messages(parent)
        txClearBtn = QPushButton("Clear")

        if debugdicts:
            debugdictList = debugdicts.split(",")
        else:
            debugdictList = []
        self.debugWidget = msgtools.debug.debug.MsgDebugWidget(debugdictList, parent)
        self.debugWidget.messageOutput.connect(self.SendMsg)
        self.debugWidget.autocompleted.connect(self.textAutocomplete)

        # tracking what reply to expect from a typed command
        self.expectedReply = None
        
        # add them to the tx layout
        txVBox = slim_vbox(self.txMsgs, txClearBtn)
        self.txSplitter = vsplitter(parent, self.txDictionary, txVBox, self.debugWidget)
        
        # create widgets for rx
        self.rx_message_list = self.configure_rx_message_list(parent)
        self.rx_messages_widget = self.configure_rx_messages_widget(parent)
        self.configure_msg_plots(parent)
        rxClearListBtn = QPushButton("Clear")
        rxSortListBtn = QPushButton("Sort")
        rxClearMsgsBtn = QPushButton("Clear")
        
        # add them to the rx layout
        rxMsgListBox = slim_vbox(self.rx_message_list, rxClearListBtn, rxSortListBtn)
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
        rxSortListBtn.clicked.connect(self.sort_rx_list)
        rxClearMsgsBtn.clicked.connect(self.clear_rx_msgs)
        
    def configure_msg_plots(self, parent):
        # dict of plot by msg_key
        self.msgPlotsByKey = {}
        self.msgPlotList = []

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

        timer = QTimer(self)
        timer.timeout.connect(self.show_rx_msg_rates)
        timer.start(1000)

        rxMessageList = QTreeWidget(parent)
        rxMessageList.setColumnCount(3)
        rxMsgHeader = QTreeWidgetItem(None, [ "Name", "Last Received", "Rx Rate" ])
        rxMessageList.setHeaderItem(rxMsgHeader)
        rxMessageList.setContextMenuPolicy(Qt.CustomContextMenu)

        rxMessageList.itemDoubleClicked.connect(self.onRxListDoubleClicked)
        rxMessageList.customContextMenuRequested.connect(lambda position : self.onRxMessageContextMenuRequested(position, rxMessageList))
        return rxMessageList
    

    def configure_rx_messages_widget(self, parent):
        self.rx_msg_widgets = {}
        rxMessagesTreeWidget = QTreeWidget(parent)
        rxMessagesTreeWidget.setColumnCount(4)
        rxMessagesTreeWidget.setDragEnabled(1)
        rxMessagesTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        rxMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        rxMessagesTreeWidget.setHeaderItem(rxMsgsHeader)
        rxMessagesTreeWidget.itemDoubleClicked.connect(self.onRxMessageFieldSelected)
        rxMessagesTreeWidget.customContextMenuRequested.connect(lambda position : self.onRxMessageContextMenuRequested(position, rxMessagesTreeWidget))
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

            messageTreeWidgetItem = txtreewidget.EditableMessageItem(self.txMsgs, messageObj, None)
            messageTreeWidgetItem.qobjectProxy.send_message.connect(self.on_tx_message_send)

    def on_open(self):
        # need to handle fields of multiple messages on same plot
        plot_count = self.settings.beginReadArray("plots")
        for i in range(plot_count):
            self.settings.setArrayIndex(i)
            plot = None
            line_count = self.settings.beginReadArray("lines")
            for j in range(line_count):
                self.settings.setArrayIndex(j)
                msg_key = self.settings.value("key")
                fieldName = self.settings.value("fieldname")
                msg_id = msg_key.split(',')[-1]
                try:
                    msgName = Messaging.MsgNameFromID[msg_id]
                except KeyError:
                    print('Error!  msg_id ' + msg_id + ' is undefined!')
                    continue
                msgClass = Messaging.MsgClassFromName[msgName]
                try:
                    if plot == None:
                        plot = self.addPlot(msgClass, msg_key, fieldName)
                    else:
                        plot.addLine(msgClass, msg_key, fieldName)
                        self.registerPlotForKey(msg_key, plot)
                except MsgPlot.PlotError as e:
                    print(e)
            self.settings.endArray()
        self.settings.endArray()

        self.txSplitter.restoreState(self.settings.value("txSplitterSizes", self.txSplitter.saveState()));
        self.rxSplitter.restoreState(self.settings.value("rxSplitterSizes", self.rxSplitter.saveState()));
        self.hSplitter.restoreState(self.settings.value("hSplitterSizes", self.hSplitter.saveState()));
        self.debugWidget.textEntryWidget.restoreState(self.settings.value("cmdHistory", self.debugWidget.textEntryWidget.saveState()));

    def on_close(self):
        self.settings.remove("plots")
        self.settings.beginWriteArray("plots")
        plotList = ""
        i = 0
        for plot in self.msgPlotList:
            self.settings.setArrayIndex(i)
            self.settings.beginWriteArray("lines")
            j = 0
            for line in plot.lines:
                self.settings.setArrayIndex(j)
                self.settings.setValue('key', line.msgKey)
                self.settings.setValue('fieldname', "%s[%d]" % (line.fieldInfo.name, line.fieldSubindex))
                j += 1
            self.settings.endArray()
            i += 1
        self.settings.endArray()
        
        # save splitter sizes and command history
        self.settings.setValue("txSplitterSizes", self.txSplitter.saveState());
        self.settings.setValue("rxSplitterSizes", self.rxSplitter.saveState());
        self.settings.setValue("hSplitterSizes",  self.hSplitter.saveState());
        self.settings.setValue("cmdHistory", self.debugWidget.textEntryWidget.saveState());
            
    def on_tx_message_send(self, msg):
        if not self.connected:
            self.OpenConnection()
        text = msgcsv.toCsv(msg)
        self.debugWidget.textEntryWidget.addText(text + " -> Msg\n> ")
        self.debugWidget.textEntryWidget.addToHistory(text)
        self.SendMsg(msg)
    
    def registerPlotForKey(self, msg_key, plot):
        if not msg_key in self.msgPlotsByKey:
            self.msgPlotsByKey[msg_key] = []
        if not plot in self.msgPlotsByKey[msg_key]:
            self.msgPlotsByKey[msg_key].append(plot)

    def addPlot(self, msgClass, msg_key, fieldName):
        plotListForKey = []
        if msg_key in self.msgPlotsByKey:
            plotListForKey = self.msgPlotsByKey[msg_key]
        else:
            self.msgPlotsByKey[msg_key] = plotListForKey
        plotName = msgClass.MsgName()
        if plottingLoaded:
            msgPlot = MsgPlot(msgClass, msg_key, fieldName)
            self.msgPlotList.append(msgPlot)
            # add a dock widget for new plot
            dockWidget = ClosableDockWidget(plotName, self, msgPlot, plotListForKey, self.msgPlotList)
            self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
            # Change title when plot is paused/resumed
            msgPlot.Paused.connect(lambda paused: dockWidget.setWindowTitle(plotName+" (PAUSED)" if paused else plotName))
            msgPlot.AddLineError.connect(lambda s: QMessageBox.warning(self, "Message Scope", s))
            # callback to register a plot to listen to a message ID.
            # this is triggered by plotting new message fields on a plot (including by drag-and-drop)
            def register_plot_for_message_key(key):
                plot = self.sender()
                self.registerPlotForKey(key, plot)
            msgPlot.RegisterForMessage.connect(lambda key: register_plot_for_message_key(key))
            plotListForKey.append(msgPlot)
            return msgPlot
        
    def onRxMessageFieldSelected(self, rxWidgetItem):
        if isinstance(rxWidgetItem, txtreewidget.FieldItem) or isinstance(rxWidgetItem, txtreewidget.FieldArrayItem):
            fieldInfo = rxWidgetItem.fieldInfo
            msg_id = hex(rxWidgetItem.msg.hdr.GetMessageID())
            msg_key = ",".join(Messaging.MsgRoute(rxWidgetItem.msg)) + "," + msg_id
            try:
                msgPlot = self.addPlot(type(rxWidgetItem.msg), msg_key, rxWidgetItem.fieldName)
                if msgPlot:
                    msgPlot.addData(rxWidgetItem.msg)
            except MsgPlot.PlotError as e:
                QMessageBox.warning(self, "Message Scope", str(e))

    def onRxMessageContextMenuRequested(self, pos, parent):
        rxWidgetItem = parent.itemAt(pos)
        if not rxWidgetItem:
            return
        msg_name = rxWidgetItem.msg.MsgName()
        msg_id = hex(rxWidgetItem.msg.hdr.GetMessageID())
        msg_key = ",".join(Messaging.MsgRoute(rxWidgetItem.msg)) + "," + msg_id
        
        menu = QMenu("Context menu", self)
        inspectAction = QAction('&Inspect', self)
        inspectAction.msg_name = msg_name
        inspectAction.msg_key = msg_key
        menu.addAction(inspectAction)
        inspectAction.triggered.connect(self.openMsgInspector)
        # add needed actions
        menu.exec(rxWidgetItem.treeWidget().viewport().mapToGlobal(pos))
    
    def openMsgInspector(self):
        sender = self.sender()

        args = []
        if self.connectionName:
            args = args + ['--connectionName='+self.connectionName]
        # If we were started with a specific msgdir, pass that on to msginspector
        try:
            self.msgdir
            args.append("--msgdir")
            args.append(self.msgdir)
        except AttributeError:
            pass
        # add the name of the message to the argument list
        args.append('--msg')
        args.append(sender.msg_name)
        #TODO do something with key!  it filters by sender/route.
        #sender.msg_key
        
        # launch msginspector with all the right args
        proc = QProcess(self)
        proc.start('msginspector', args)

                
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
            msg_list_item.rx_count = 1
            msg_list_item.avg_rate = 1.0

            self.rx_message_list.addTopLevelItem(msg_list_item)
            self.rx_message_list.resizeColumnToContents(0)
            self.rx_msg_list[msg_key] = msg_list_item

        self.rx_msg_list[msg_key].setText(1, rx_time.strftime('%H:%M:%S.%f')[:-3])
        self.rx_msg_list[msg_key].msg = msg
        self.rx_msg_list[msg_key].rx_count += 1

    def show_rx_msg_rates(self):
        weight = 0.5
        for msg_key, widget in self.rx_msg_list.items():
            rate = float(widget.rx_count)
            widget.rx_count = 0
            widget.avg_rate = weight * widget.avg_rate + (1-weight) * rate

            if widget.avg_rate > 0.05:
                output = "{0:0.1f} Hz".format(widget.avg_rate)
            elif widget.avg_rate > 0.01:
                output = "0 Hz"
            else:
                output = "-- Hz"

            self.rx_msg_list[msg_key].setText(2, output)

    def add_message_to_rx_tree(self, msg_key, msg):
        if not msg_key in self.rx_msg_widgets:
            msg_widget = txtreewidget.MessageItem(self.rx_messages_widget, msg, msg_key)
            self.rx_msg_widgets[msg_key] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)
            self.rx_messages_widget.resizeColumnToContents(0)

    def display_message_in_rx_tree(self, msg_key, msg):
        if msg_key in self.rx_msg_widgets:
            self.rx_msg_widgets[msg_key].set_msg_buffer(msg.rawBuffer())
    
    def display_message_in_plots(self, msg_key, msg):
        if msg_key in self.msgPlotsByKey:
            plotListForKey = self.msgPlotsByKey[msg_key]
            for plot in plotListForKey:
                plot.addData(msg)
    
    def clear_rx_list(self):
        self.rx_msg_list = {}
        self.rx_message_list.clear()

    def sort_rx_list(self):
        self.rx_message_list.setSortingEnabled(not self.rx_message_list.isSortingEnabled())

    def clear_rx_msgs(self):
        self.rx_msg_widgets = {}
        self.rx_messages_widget.clear()

    def clear_tx(self):
        self.txMsgs.clear()
    
    # when text edit autocomplete occurs, find the corresponding item
    # in the tx dictionary
    def textAutocomplete(self, autocomplete):
        def item_matches(item, sequence):
            # look in reverse at sequence of parts, verifying
            # that each part matches the item and it's parents.
            for part in reversed(sequence):
                if part == '':
                    continue
                if item.text(0) != part:
                    return False
                item = item.parent()
            return True
        msgname_parts = autocomplete.replace(',', '').split('.')
        for msgpart in msgname_parts:
            # find all matches...
            matches = self.txDictionary.findItems(msgpart, Qt.MatchExactly | Qt.MatchRecursive, 0)
            for item in matches:
                # ... then for each match, make sure all parts match
                if item_matches(item, msgname_parts):
                    self.txDictionary.setCurrentItem(item)

def main():
    # Setup a command line processor...
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
    parser.add_argument('--debugdicts', help=''''Dictionaries to use for debug message format strings.''')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(args)
    msgScopeGui.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
