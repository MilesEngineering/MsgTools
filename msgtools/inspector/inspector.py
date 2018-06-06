#!/usr/bin/env python3
import struct
import sys
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

DESCRIPTION='''MsgInspector allows you to connect to a MsgServer and inspect messages as they arrive.
    It is similar to MsgScope but presents data in a time linear format with compact details.  Each message
    type grouped into it's own tab'''

class MsgInspector(msgtools.lib.gui.Gui):
    def __init__(self, parent=None):
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('--msgfields', nargs='+', help='''One or more msgName:fieldName specifiers which we'll use to 
            display filtered message views. Example --keyfields Printf/LineNumber Network.Note/Text.  Implies  the --msg option 
            for each message specified, and overrides --msg if supplied''')
        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)
        args=parser.parse_args()

        msgtools.lib.gui.Gui.__init__(self, "Message Inspector 0.1", args, parent)

        self.keyFields = {}

        # Process our msg/keyfields
        if args.msgfields is not None:
            self.allowedMessages = []   # Override --msg
            for msgfield in args.msgfields:
                msgName,fieldName = msgfield.split('/')

                if msgName not in Messaging.MsgIDFromName:
                    print('{0} is an unknown message name.'.format(msgName))
                    sys.exit(1)

                if isinstance(fieldName, str) is False:
                    print(msgfield, ': You may only specify one field name per message.')
                    sys.exit(1)

                MsgClass = Messaging.MsgClassFromName[msgName]
                if hasattr(MsgClass, 'fields'):
                    fieldNames = [field.name for field in MsgClass.fields]
                    if fieldName not in fieldNames:
                        print('{0} is not a field of {1}.  Valid fields are: {2}'.format(fieldName, msgName,
                            fieldNames))
                        sys.exit(1)

                self.allowedMessages.append(msgName)
                self.keyFields[msgName] = fieldName

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
            msgKey += " ("+",".join(msgRoute)+")"

        if(not(msgKey in self.msgWidgets)):
            # create a new tree widget
            keyField = self.keyFields.get(msg.MsgName(), None)
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
    msgApp = MsgInspector()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
