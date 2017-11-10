#!/usr/bin/env python3
import struct
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

class MsgInspector(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        msgtools.lib.gui.Gui.__init__(self, "Message Inspector 0.1", argv, [], parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
        
        # whether we should autoscroll as data is added
        self.autoscroll = 1
        
        # menu items to change view
        clearAction = QtWidgets.QAction('&Clear', self)
        clearAllAction = QtWidgets.QAction('Clear &All', self)
        self.scrollAction = QtWidgets.QAction('&Scroll', self)
        self.scrollAction.setCheckable(1)
        self.scrollAction.setChecked(self.autoscroll)

        menubar = self.menuBar()
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(clearAction)
        viewMenu.addAction(clearAllAction)
        viewMenu.addAction(self.scrollAction)

        clearAction.triggered.connect(self.clearTab)
        clearAllAction.triggered.connect(self.clearAllTabs)
        self.scrollAction.triggered.connect(self.switchScroll)
    
    def clearTab(self):
        self.tabWidget.currentWidget().clear()
    
    def clearAllTabs(self):
        for id, widget in self.msgWidgets.items():
            widget.clear()
        
    def switchScroll(self):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def tableDataDoubleClicked(self, treeWidgetItem, column):
        self.autoscroll = not self.autoscroll
        self.scrollAction.setChecked(self.autoscroll)

    def ProcessMessage(self, msg):
        hdr = msg.hdr
        
        # create identifying string for type and source of message
        msgRoute = Messaging.MsgRoute(msg)
        msgKey = msg.MsgName()
        if len(msgRoute) > 0 and not(all ("0" == a for a in msgRoute)):
            msgKey += " ("+"->".join(msgRoute)+")"

        if self.allowedMessages:
            if not msg.MsgName() in self.allowedMessages:
                return

        if(not(msgKey in self.msgWidgets)):
            # create a new tree widget
            try:
                keyField = self.keyFields[msg.MsgName()]
            except KeyError:
                keyField = None
            msgWidget = msgtools.lib.gui.MsgTreeWidget(type(msg), keyField)

            # connect to double-clicked signal to change scrolling globally
            msgWidget.itemDoubleClicked.connect(self.tableDataDoubleClicked)
            
            # add it to the tab widget, so the user can see it
            self.tabWidget.addTab(msgWidget, msgKey)
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[msgKey] = msgWidget
        
        # give the data to the widget
        self.msgWidgets[msgKey].addData(msg, self.autoscroll)

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
