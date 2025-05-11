#!/usr/bin/env python3
import argparse
import ast
import collections
import datetime
import functools
import os
import sys
import struct
import yaml

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

import msgtools.scope.launcher as launcher

import msgtools.lib.txtreewidget as txtreewidget
plotting_loaded=False
try:
    from msgtools.lib.msgplot import MsgPlot, PlotRegistry
    plotting_loaded=True
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
    def __init__(self, name, parent, widget, plot_registry):
        super(QDockWidget,self).__init__(name, parent)
        self.setObjectName(name)
        self.setWidget(widget)
        self.plot_registry = plot_registry

    def closeEvent(self, event):
        self.plot_registry.remove_plot(self.widget())
        self.parent().removeDockWidget(self)
        # Both of the below were added to try to get open plots to close
        # when we open new YAML configs.  Even so, the dockable windows don't
        # close and I've no idea why.
        event.accept()
        super().closeEvent(event)

class MessageScopeGui(msgtools.lib.gui.Gui):
    DEFAULT_WINDOW_WIDTH  = 600
    DEFAULT_WINDOW_HEIGHT = 600
    def __init__(self, args, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Message Scope 0.1", args, parent)
        self.setWindowIcon(QIcon(launcher.info().icon_filename))

        # Detection of things changing that should go into the config file
        self.connectionNameChanged.connect(self.set_config_file_modified_true)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        self.configure_gui(parent, args.debugdicts, args.config)
        
        self.txDictionary.ReadTxDictionary()

    # Override resizeEvent so we can mark that our settings changed.
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_config_file_modified_true()

    def configure_gui(self, parent, debugdicts, config):
        # Set to default size, but this will be overridden with saved size
        # if there's a saved size, before the user sees the window.
        self.resize(MessageScopeGui.DEFAULT_WINDOW_WIDTH, MessageScopeGui.DEFAULT_WINDOW_HEIGHT)

        # Add a menu to open or save configuration files
        self.set_config_filename(config)
        self.config_file_modified = None
        new_action = QAction(QIcon.fromTheme("document-new"), '&New', self)
        open_action = QAction(QIcon.fromTheme("document-open"), '&Open', self)
        close_action = QAction(QIcon.fromTheme("document-close"), '&Close', self)
        save_action = QAction(QIcon.fromTheme("document-save"), '&Save', self)
        save_as_action = QAction(QIcon.fromTheme("document-save-as"), 'Save &As', self)

        # Add menu to start of menubar.  Believe it or not, you *have* to
        # call menubar.addMenu() to create the menu (not just QMenu()), and
        # then you have to call menubar.insertMenu(before, m), not anything
        # sensible like menubar.moveMenu().
        # Also you have to insert it before an action, not another menu!
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(close_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        ret = self.menuBar().insertMenu(self.connectMenu.menuAction(), file_menu)

        new_action.triggered.connect(self.file_new_or_close_action)
        open_action.triggered.connect(self.file_open_action)
        save_action.triggered.connect(self.file_save_action)
        save_as_action.triggered.connect(self.file_save_as_action)
        close_action.triggered.connect(self.file_new_or_close_action)

        # create widgets for tx
        self.txDictionary = self.configure_tx_dictionary()
        self.txMsgs = self.configure_tx_messages(parent)
        txClearBtn = QPushButton("Clear")

        if debugdicts:
            debugdictList = debugdicts.split(",")
        else:
            debugdictList = []
        self.debugWidget = msgtools.debug.debug.MsgDebugWidget(debugdictList, parent)
        self.debugWidget.messageOutput.connect(self.SendMsg)
        self.debugWidget.autocompleted.connect(self.textAutocomplete)
        self.debugWidget.statusUpdate.connect(self.statusUpdate)

        # tracking what reply to expect from a typed command
        self.expectedReply = None
        
        # add them to the tx layout
        txVBox = slim_vbox(self.txMsgs, txClearBtn)
        self.txSplitter = vsplitter(parent, self.txDictionary, txVBox, self.debugWidget)
        self.txSplitter.splitterMoved.connect(self.set_config_file_modified_true)
        
        # create widgets for rx
        self.rx_message_list = self.configure_rx_message_list()
        self.rx_messages_widget = self.configure_rx_messages_widget(parent)
        if plotting_loaded:
            self.plot_registry = PlotRegistry()
            self.plot_registry.plots_changed.connect(self.set_config_file_modified_true)
        else:
            self.plot_registry = None
        rxClearListBtn = QPushButton("Clear")
        rxClearMsgsBtn = QPushButton("Clear")
        
        # add them to the rx layout
        rxMsgListBox = slim_vbox(self.rx_message_list, rxClearListBtn)
        rxMsgsBox = slim_vbox(self.rx_messages_widget, rxClearMsgsBtn)
        self.rxSplitter = vsplitter(parent, rxMsgListBox, rxMsgsBox)
        self.rxSplitter.splitterMoved.connect(self.set_config_file_modified_true)

        # top level horizontal splitter to divide the screen
        self.hSplitter = QSplitter(parent)
        self.hSplitter.addWidget(self.txSplitter)
        self.hSplitter.addWidget(self.rxSplitter)
        self.hSplitter.splitterMoved.connect(self.set_config_file_modified_true)

        self.setCentralWidget(self.hSplitter)
    
        # connect signals for 'clear' buttons
        txClearBtn.clicked.connect(self.clear_tx)
        rxClearListBtn.clicked.connect(self.clear_rx_list)
        rxClearMsgsBtn.clicked.connect(self.clear_rx_msgs)

    class TxDictionaryItem(QTreeWidgetItem):
        index = 0
        def __init__(self, parent):
            super(QTreeWidgetItem, self).__init__(parent)
            # Remember the index that messages were created with, because
            # that is the same as the order of the messages in the YAML.
            self.initial_order_index = MessageScopeGui.TxDictionaryItem.index
            MessageScopeGui.TxDictionaryItem.index += 1

        def __lt__(self, otherItem):
            # return comparison based on initial sort order, which is based
            # on the order messages are defined in the YAML.
            if not self.treeWidget().header().isSortIndicatorShown():
                return self.initial_order_index < otherItem.initial_order_index
            column = self.treeWidget().sortColumn()
            return self.text(column) < otherItem.text(column)

    class TxDictionary(QTreeWidget):
        def __init__(self):
            super(MessageScopeGui.TxDictionary, self).__init__()
            self.setHeaderLabels(["Transmit Dictionary"])
            # configure the header so we can click on it to sort
            self.header().setSectionsClickable(True)
            self.header().setSortIndicatorShown(False)
            self.header().sectionClicked.connect(self.tableHeaderClicked)
        
        def isSorted(self):
            return self.header().isSortIndicatorShown()
        
        def setSorted(self, sorted):
            self.header().setSortIndicatorShown(sorted)
            self.sortItems(0, Qt.AscendingOrder)

        def tableHeaderClicked(self, column):
            if self.header().isSortIndicatorShown():
                self.header().setSortIndicatorShown(False)
            else:
                self.header().setSortIndicatorShown(True)

            # Always sort so that top-level items are sorted, but if our
            # sortIndicator isn't shown, children will sort themselves
            # according to their initial order and not alphabetically.
            self.sortItems(column, Qt.AscendingOrder)

        def ReadTxDictionary(self):
            #print("Tx Dictionary:")
            # We want to read the dictionary in numerical order, but MsgNameFromID
            # has keys that are hex strings, so create a dictionary of integer ID
            # to hex ID and iterate over the sorted version of integer IDs.
            msg_id_from_int = {}
            for msg_id in Messaging.MsgNameFromID:
                msg_id_from_int[int(msg_id, 16)] = msg_id
            for int_id in sorted(msg_id_from_int):
                id = msg_id_from_int[int_id]
                name = Messaging.MsgNameFromID[id]
                components = name.split('.')
                dirs = components[:-1]
                msgName = components[-1]
                
                parentWidget = self
                parentPath = ""
                for dir in dirs:
                    # find the node that matches the directory we're looking for
                    dirItemMatches = self.findItems(dir, Qt.MatchExactly | Qt.MatchRecursive, 0)
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
                        if parentWidget == self:
                            newWidget = QTreeWidgetItem(parentWidget)
                            newWidget.initial_order_index = -1
                        else:
                            newWidget = MessageScopeGui.TxDictionaryItem(parentWidget)
                        newWidget.setText(0, dir)
                        newWidget.parentPath = parentPath
                        parentWidget = newWidget
                    parentPath += dir + "."
                msgItem = MessageScopeGui.TxDictionaryItem(parentWidget)
                msgItem.setText(0, msgName)
                msgItem.msgName = name
            self.sortByColumn(0, Qt.AscendingOrder)

    def configure_tx_dictionary(self):
        txDictionary = MessageScopeGui.TxDictionary()
        txDictionary.itemDoubleClicked.connect(self.onTxMessageSelected)
        return txDictionary

    def configure_tx_messages(self, parent):
        txMsgs = QTreeWidget(parent)
        txMsgs.setItemDelegate(txtreewidget.NoEditDelegate(parent, txMsgs))
        txMsgs.setColumnCount(4)
        
        txMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        
        txMsgs.setHeaderItem(txMsgsHeader)
        return txMsgs

    class RxMessageListItem(QTreeWidgetItem):
        def __init__(self, msg_key, msg, rx_time):
            widget_name = msg.MsgName()
            msg_route = Messaging.MsgRoute(msg)
            if len(msg_route) > 0 and not(all ("0" == a for a in msg_route)):
                widget_name += " ("+",".join(msg_route)+")"
            super(MessageScopeGui.RxMessageListItem, self).__init__([ widget_name, rx_time.strftime('%H:%M:%S.%f')[:-3], "- Hz" ])
            self.msg_key = msg_key
            self.msg = msg
            self.rx_count = 1
            self.avg_rate = 1.0

        def __lt__(self, otherItem):
            column = self.treeWidget().sortColumn()
            if column == 2:
                return self.avg_rate < otherItem.avg_rate
            try:
                return float(self.text(column)) < float(otherItem.text(column))
            except ValueError:
                return self.text(column) < otherItem.text(column)

    class RxMessageList(QTreeWidget):
        def __init__(self):
            super(MessageScopeGui.RxMessageList, self).__init__()
            self.setColumnCount(3)
            rxMsgHeader = QTreeWidgetItem(None, [ "Name", "Last Received", "Rx Rate" ])
            self.setHeaderItem(rxMsgHeader)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            # configure the header so we can click on it to sort
            self.header().setSectionsClickable(True)
            self.header().setSortIndicatorShown(False)
            self.keyField = None
            self.sortOrder = Qt.AscendingOrder
            self.header().sectionClicked.connect(self.tableHeaderClicked)

            self.items_by_key = {}

            timer = QTimer(self)
            timer.timeout.connect(self.show_rx_msg_rates)
            timer.start(1000)

        def tableHeaderClicked(self, column):
            self.header().setSortIndicatorShown(True)
            fieldName = self.headerItem().text(column)
            if self.keyField == None or self.keyField != fieldName:
                self.keyField = fieldName
                self.sortOrder = Qt.AscendingOrder
            else:
                self.sortOrder = Qt.DescendingOrder if self.sortOrder == Qt.AscendingOrder else Qt.AscendingOrder
            self.header().setSortIndicator(column, self.sortOrder)
            self.sortItems(column, self.sortOrder)

        def show_rx_msg_rates(self):
            weight = 0.5
            for msg_key, widget in self.items_by_key.items():
                rate = float(widget.rx_count)
                widget.rx_count = 0
                widget.avg_rate = (1-weight) * widget.avg_rate + weight * rate

                if widget.avg_rate > 0.05:
                    output = "{0:0.1f} Hz".format(widget.avg_rate)
                elif widget.avg_rate > 0.01:
                    output = "0 Hz"
                else:
                    output = "-- Hz"

                if self.items_by_key[msg_key].rx_time_changed:
                    self.items_by_key[msg_key].setText(1, self.items_by_key[msg_key].rx_time.strftime('%H:%M:%S.%f')[:-3])
                self.items_by_key[msg_key].rx_time_changed = False
                self.items_by_key[msg_key].setText(2, output)

        def updateMessage(self, msg_key, msg):
            rx_time = datetime.datetime.now()
            if not msg_key in self.items_by_key:
                msg_list_item = MessageScopeGui.RxMessageListItem(msg_key, msg, rx_time)

                # Add an item at the end of the list
                self.addTopLevelItem(msg_list_item)
                # Hide the sort indicator, since we added at the end and sorting has been broken
                self.header().setSortIndicatorShown(False)
                self.resizeColumnToContents(0)
                self.items_by_key[msg_key] = msg_list_item

            self.items_by_key[msg_key].rx_time = rx_time
            self.items_by_key[msg_key].rx_time_changed = True
            self.items_by_key[msg_key].msg = msg
            self.items_by_key[msg_key].rx_count += 1
        
        def clear(self):
            self.items_by_key = {}
            super(MessageScopeGui.RxMessageList, self).clear()

    def configure_rx_message_list(self):
        rxMessageList = MessageScopeGui.RxMessageList()
        rxMessageList.itemDoubleClicked.connect(self.onRxListDoubleClicked)
        rxMessageList.customContextMenuRequested.connect(lambda position : self.onRxMessageContextMenuRequested(position, rxMessageList))
        return rxMessageList
    

    def configure_rx_messages_widget(self, parent):
        self.rx_msg_widgets = {}
        rxMessagesTreeWidget = QTreeWidget(parent)
        rxMessagesTreeWidget.setItemDelegate(txtreewidget.NoEditDelegate(parent, self.rx_msg_widgets))

        rxMessagesTreeWidget.setColumnCount(4)
        rxMessagesTreeWidget.setDragEnabled(1)
        rxMessagesTreeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        rxMsgsHeader = QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
        rxMessagesTreeWidget.setHeaderItem(rxMsgsHeader)
        rxMessagesTreeWidget.itemDoubleClicked.connect(self.onRxMessageFieldSelected)
        rxMessagesTreeWidget.customContextMenuRequested.connect(lambda position : self.onRxMessageContextMenuRequested(position, rxMessagesTreeWidget))
        return rxMessagesTreeWidget


    def onTxMessageSelected(self, txListWidgetItem):
        # directories have children but messages don't, so only add messages by verifying the childCount is zero
        if txListWidgetItem.childCount() == 0:
            messageName = txListWidgetItem.msgName
            # Always add to TX panel even if the same message class may already exist
            # since we may want to send the same message with different contents/header/rates.
            message_class = Messaging.MsgClassFromName[messageName]
            messageObj = message_class() # invoke constructor

            messageTreeWidgetItem = txtreewidget.MessageItem(editable=True, tree_widget=self.txMsgs, msg=messageObj, msg_key=None)
            messageTreeWidgetItem.qobjectProxy.send_message.connect(self.on_tx_message_send)

    # This is for using our self.settings QSettings object, to read whatever was configured last time we ran.
    def readLastSettings(self):
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
                        self.plot_registry.register(msg_key, plot)
                except MsgPlot.PlotError as e:
                    print(e)
            self.settings.endArray()
        self.settings.endArray()
        
        self.txDictionary.setSorted(self.settings.value("txDictionarySorted", False, type=bool))

        self.txSplitter.restoreState(self.settings.value("txSplitterSizes", self.txSplitter.saveState()));
        self.rxSplitter.restoreState(self.settings.value("rxSplitterSizes", self.rxSplitter.saveState()));
        self.hSplitter.restoreState(self.settings.value("hSplitterSizes", self.hSplitter.saveState()));
        self.debugWidget.textEntryWidget.restoreState(self.settings.value("cmdHistory", self.debugWidget.textEntryWidget.saveState()));

    # This is for using our self.settings QSettings object, to write whatever was
    # configured as we close, so it can be used next time we run.
    def writeLastSettings(self):
        self.settings.remove("plots")
        self.settings.beginWriteArray("plots")
        plotList = ""
        i = 0
        for plot in self.plot_registry.plot_list:
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
        
        # remember if the Tx Dictionary was sorted
        self.settings.setValue("txDictionarySorted", self.txDictionary.isSorted())

        # save splitter sizes and command history
        self.settings.setValue("txSplitterSizes", self.txSplitter.saveState());
        self.settings.setValue("rxSplitterSizes", self.rxSplitter.saveState());
        self.settings.setValue("hSplitterSizes",  self.hSplitter.saveState());
        self.settings.setValue("cmdHistory", self.debugWidget.textEntryWidget.saveState());

    def on_open(self):
        if self.config_filename:
            self.load_config_file(self.config_filename, opening_file_on_startup=True)
        else:
            self.readLastSettings()

    def on_close(self):
        if self.config_filename:
            self.open_maybe_save_dialog(give_cancel_option=False)
        else:
            self.writeLastSettings()

    def clear_settings_struct(self):
        # Close all the plots
        for dock_widget in self.findChildren(ClosableDockWidget):
            # Trying this because close() doesn't work.
            if dock_widget.isFloating():
                dock_widget.setFloating(False)
            dock_widget.close()
        self.plot_registry.clear()
        
        # Restore window size to defaults
        self.resize(MessageScopeGui.DEFAULT_WINDOW_WIDTH, MessageScopeGui.DEFAULT_WINDOW_HEIGHT)

    def parse_settings_struct(self, s):
        def str_to_b_get(d, key, default):
            try:
                v = d[key]
                ba = bytearray(ast.literal_eval(v))
            except:
                return default
            return ba

        # Open plots for the stored configuration
        for plot_setting in s["plots"]:
            plot = None
            for line_setting in plot_setting["lines"]:
                msg_key = line_setting["key"]
                fieldName = line_setting["fieldname"]
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
                        self.plot_registry.register(msg_key, plot)
                except MsgPlot.PlotError as e:
                    print(e)
                
        self.txDictionary.setSorted(s.get("txDictionarySorted", False))
        self.txSplitter.restoreState(str_to_b_get(s, "txSplitterSizes", self.txSplitter.saveState()))
        self.rxSplitter.restoreState(str_to_b_get(s, "rxSplitterSizes", self.rxSplitter.saveState()))
        self.hSplitter.restoreState(str_to_b_get(s, "hSplitterSizes", self.hSplitter.saveState()))
        self.debugWidget.textEntryWidget.restoreStateStructure(s.get("cmdHistory", self.debugWidget.textEntryWidget.saveState()))
        self.restoreGeometry(str_to_b_get(s, "geometry", QByteArray()))
        self.restoreState(str_to_b_get(s, "windowState", QByteArray()))
        if "connection_name" in s:
            cxn = s["connection_name"]
            # If the connection name needs to change, then change it and reconnect.
            if self.connectionName != cxn:
                self.connectionName = cxn
                self.OpenConnection()

    def create_settings_struct(self):
        def line_settings(line):
            return {'key': line.msgKey, 'fieldname': "%s[%d]" % (line.fieldInfo.name, line.fieldSubindex)}
        def plot_settings(plot):
            return {'lines': [line_settings(line) for line in plot.lines]}
        settings = {
            'plots': [plot_settings(plot) for plot in self.plot_registry.plot_list],
            "txSplitterSizes":    str(self.txSplitter.saveState()),
            "txDictionarySorted": self.txDictionary.isSorted(),
            "rxSplitterSizes":    str(self.rxSplitter.saveState()),
            "hSplitterSizes":     str(self.hSplitter.saveState()),
            "cmdHistory":         self.debugWidget.textEntryWidget.saveStateStructure(),
            "geometry":           str(self.saveGeometry()),
            "windowState":        str(self.saveState()),
            "connection_name":    self.connectionName
        }
        return settings

    def on_tx_message_send(self, msg):
        if not self.connected:
            self.OpenConnection()
        text = msgcsv.toCsv(msg)
        self.debugWidget.textEntryWidget.addText(text + " -> Msg\n> ")
        self.debugWidget.textEntryWidget.addToHistory(text)
        self.SendMsg(msg)

    def addPlot(self, msgClass, msg_key, fieldName):
        plotName = msgClass.MsgName()
        if plotting_loaded:
            plot = MsgPlot(msgClass, msg_key, fieldName, plot_registry=self.plot_registry)
            self.plot_registry.register(msg_key, plot)
            # add a dock widget for new plot
            dockWidget = ClosableDockWidget(plotName, self, plot, plot_registry=self.plot_registry)
            self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
            # Change title when plot is paused/resumed
            plot.Paused.connect(lambda paused: dockWidget.setWindowTitle(plotName+" (PAUSED)" if paused else plotName))
            plot.AddLineError.connect(lambda s: QMessageBox.warning(self, "Message Scope", s))
            return plot

    def onRxMessageFieldSelected(self, rxWidgetItem):
        if isinstance(rxWidgetItem, txtreewidget.FieldItem) or isinstance(rxWidgetItem, txtreewidget.FieldArrayItem):
            fieldInfo = rxWidgetItem.fieldInfo
            msg_id = hex(rxWidgetItem.msg.hdr.GetMessageID())
            msg_key = ",".join(Messaging.MsgRoute(rxWidgetItem.msg)) + "," + msg_id
            try:
                self.set_config_file_modified(True)
                plot = self.addPlot(type(rxWidgetItem.msg), msg_key, rxWidgetItem.fieldName)
                if plot:
                    plot.addData(rxWidgetItem.msg)
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
        self.rx_message_list.updateMessage(msg_key, msg)

    def add_message_to_rx_tree(self, msg_key, msg):
        if not msg_key in self.rx_msg_widgets:
            msg_widget = txtreewidget.MessageItem(editable=False, tree_widget=self.rx_messages_widget, msg=msg, msg_key=msg_key)
            self.rx_msg_widgets[msg_key] = msg_widget
            self.rx_messages_widget.addTopLevelItem(msg_widget)
            self.rx_messages_widget.resizeColumnToContents(0)

    def display_message_in_rx_tree(self, msg_key, msg):
        if msg_key in self.rx_msg_widgets:
            self.rx_msg_widgets[msg_key].set_msg_buffer(msg.rawBuffer())
    
    def display_message_in_plots(self, msg_key, msg):
        self.plot_registry.add_plot_data(msg_key, msg)
    
    def clear_rx_list(self):
        self.rx_message_list.clear()

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

    def file_open_action(self):
        if self.open_maybe_save_dialog():
            filename, _ = QFileDialog.getOpenFileName(self)
            if filename:
                self.load_config_file(filename)
    
    def file_save_action(self):
        if self.config_filename == '':
            return self.file_save_as_action()
        else:
            return self.save_file(self.config_filename)
    
    def file_save_as_action(self):
        filename, _ = QFileDialog.getSaveFileName(self,
            "Save msgscope configuration","","MsgScope Files (*.msgscope)")
        if not filename:
            return False
        return self.save_file(filename)

    def file_new_or_close_action(self):
        self.set_config_filename('')
        # Get rid of all user customizations (plots, but maybe also Tx message objects with value?)
        self.clear_settings_struct()
        self.set_config_file_modified(False)

    def set_config_filename(self, filename):
        self.config_filename = filename

    def load_config_file(self, filename, opening_file_on_startup=False):
        if filename != self.config_filename:
            self.set_config_filename(filename)
        
        if not opening_file_on_startup:
            self.clear_settings_struct()
        try:
            with open(filename, 'r') as file:
                s = yaml.safe_load(file)
                self.parse_settings_struct(s)
                # Right after we've loaded settings, everything matches the file.
                self.set_config_file_modified(False)
        except (IOError, FileNotFoundError):
            QtWidgets.QMessageBox.warning(self, "Application", "Cannot read file %s" % (filename))
            return
        else:
            self.set_config_file_modified(False)

    # Convenience function that can be connected to signals
    # that occur when any settings change.
    def set_config_file_modified_true(self):
        self.set_config_file_modified(True)

    def set_config_file_modified(self, modified):
        # If it's already marked as modified, don't redo anything here.
        # This function gets called every time our window is resized and when splitters
        # move, so it can get called a lot when the user plays with the GUI.
        if self.config_file_modified == modified:
            return

        self.config_file_modified = modified
        title = self.name
        if self.config_filename:
            title += " -- Config File %s" % self.config_filename
            if self.config_file_modified:
                title = title + " *"
        self.setWindowTitle(title)
    
    def open_maybe_save_dialog(self, give_cancel_option=True):
        if not self.config_file_modified:
            return True
        options = QMessageBox.Save | QMessageBox.Discard
        if give_cancel_option:
            options |= QMessageBox.Cancel
        ret = QMessageBox.warning(self, "Application",
            "The document has been modified.\nDo you want to save your changes?", options);
        if ret == QMessageBox.Save:
            return self.save_file(self.config_filename)
        elif ret == QMessageBox.Cancel:
            return False

        return True

    def save_file(self, filename):
        try:
            file = open(filename, 'w')
        except IOError:
            QMessageBox.warning(self, "Application", "Cannot write file %s" % (filename))
            return False
        else:
            with file as outfile:
                # write settings to file
                self.set_config_filename(filename)
                self.statusBar().showMessage("File saved", 2000)
                settings_struct = self.create_settings_struct()
                yaml.dump(settings_struct, outfile, sort_keys=False, default_flow_style=False)
                return True
        return True

def main():
    # Setup a command line processor...
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
    parser.add_argument('--debugdicts', help=''''Dictionaries to use for debug message format strings.''')
    parser.add_argument('--config', help=''''GUI Configuration file.''')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    msgScopeGui = MessageScopeGui(args)
    msgScopeGui.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
