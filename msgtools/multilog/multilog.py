#!/usr/bin/env python3

# TODO
#   add hotkey support (already reading options for it on cmdline)
#  Add annotation field.
#         text gets inserted in log whenever you hit enter in annotation box or click 'note' button next to annotate box.

import sys
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
from time import strftime

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui
import msgtools.lib.txtreewidget

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

DESCRIPTION='''
    MultiLog presents a UI that lets you control logging of messages on an 
    individual basis, and send and receive messages pressing a button 
    starts/stops a log file.  Underscores in label or field are replaced 
    with spaces for display (to make entering command-line args easier)

    Log filenames will be composed like so:
        YEAR_MONTH_DAY.TEXT1.TEXT2.TAG1.log'''

EPILOG='''
    Example usage: multilog --fields LABEL1 LABEL2 --buttons hotkey:X,tag:TAG1,label:LABEL3  
    hotkey:X,tag:TAG2,label:LABEL4 --show MSGNAME MSGNAME2 --plot MSGNAME[fieldname1,fieldname2] 
    MSGNAME2[fieldname3,fieldname4] --send MSGNAME MSGNAME2
    '''

def removePrefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text
    
class Multilog(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('--fields', nargs='+', default=[], 
            help='''each --field argument adds a text field named the specified LABEL, and 
                    the value of the text field will become part of the filename.  
                    Example argument: LABEL1''')
        parser.add_argument('--buttons', nargs='+', default=[], help='''each --button 
                    argument adds a pushbutton named for the specified LABEL, with a 
                    hotkey of the specified key, and the tag value will become part of 
                    the filename.  Example argument: hotkey:X,tag:TAG1,label:LABEL1''')
        parser.add_argument('--show', nargs='+', default=[], 
            help='each --show argument adds a table view of that MSGNAME')
        parser.add_argument('--plot', nargs='+', default=[], help='''each --plot argument 
                    adds a plot of the fields within MSGNAME.  If fields left off, all 
                    fields are plotted.  Add [idx] to field name if array and want element
                    other than element zero.  Example argument: MSGNAME(fieldname1,fieldname2[2])''')
        parser.add_argument('--send', nargs='+', default=[], help='''each --send argument 
                    is a message name that adds a tree view to edit a message with a 'send' 
                    button to send it.  Example argument: MSGNAME''')

        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)

        args=parser.parse_args([arg for arg in argv[1:] if not '=' in arg])

        msgtools.lib.gui.Gui.__init__(self, "Multilog 0.1", args, parent)
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)
        
        # handling of messages by sub-widgets
        self.msgHandlers = {}

        # tab widget to show multiple messages, one per tab
        widget = QtWidgets.QWidget(self)
        vLayout = QtWidgets.QVBoxLayout(widget)
        self.setCentralWidget(widget)
        self.statusMsg = QtWidgets.QLabel("NOT logging")
        vLayout.addWidget(self.statusMsg)

        hLayout = QtWidgets.QHBoxLayout()
        vLayout.addLayout(hLayout)
        lvLayout = QtWidgets.QVBoxLayout()
        rvLayout = QtWidgets.QVBoxLayout()
        hLayout.addLayout(lvLayout)
        hLayout.addLayout(rvLayout)

        splitter = QtWidgets.QSplitter(parent)
        splitter.setOrientation(QtCore.Qt.Vertical)
        vLayout.addWidget(splitter)
        
        self.lineEdits = []
        self.buttons = []
        self.activeLogButton = None
        txMsgs = None

        # Process command line args
        for arg in argv[1:]:
            argComponentList = arg.split("=", 1)
            if len(argComponentList) < 2:
                continue
            argname = argComponentList[0]
            argvalue = argComponentList[1]
            if argname == '--field':
                field = argvalue
                label = field.replace("_"," ")

                # add text field
                lvLayout.addWidget(QtWidgets.QLabel(label))
                lineEdit = QtWidgets.QLineEdit()
                rvLayout.addWidget(lineEdit)
                self.lineEdits.append(lineEdit)
            if argname == '--button':
                button = argvalue
                parts = button.split(",")
                options = {}
                for option in parts:
                    key, value = option.split(":")
                    options[key] = value

                # add button
                label = options["label"].replace("_"," ")
                button = QtWidgets.QPushButton(label)
                # how to set hot key?  do it at window level, or at button level?  or something else?
                #button.hotKey = options["hotkey"]
                button.label = label
                self.buttons.append(button)
                if "tag" in options:
                    button.tag = options["tag"]
                else:
                    button.tag = None
                vLayout.addWidget(button)
                
                button.clicked.connect(self.HandleButtonPress)
            if argname == '--show':
                msgname = argvalue
                subWidget = QtWidgets.QWidget()
                subLayout = QtWidgets.QVBoxLayout()
                subWidget.setLayout(subLayout)
                splitter.addWidget(subWidget)
                subLayout.addWidget(QtWidgets.QLabel(msgname))
                msgClass = Messaging.MsgClassFromName[msgname]
                msgWidget = msgtools.lib.gui.MsgTreeWidget(msgClass, None, 1, 1)
                subLayout.addWidget(msgWidget)
                if not msgClass.ID in self.msgHandlers:
                    self.msgHandlers[msgClass.ID] = []
                self.msgHandlers[msgClass.ID].append(msgWidget)
            if argname == '--plot':
                plotarg = argvalue
                print("plot " + plotarg)
                if plottingLoaded:
                    if "=" in plotarg:
                        split = plotarg.split("=")
                        msgname = split[0]
                        fieldNames = split[1].split(',')
                    else:
                        msgname = plotarg
                        fieldNames = []
                    subWidget = QtWidgets.QWidget()
                    self.plotlayout = QtWidgets.QVBoxLayout()
                    subWidget.setLayout(self.plotlayout)
                    splitter.addWidget(subWidget)
                    msgClass = Messaging.MsgClassFromName[msgname]
                    msgPlot = None
                    msgPlot = MsgPlot.plotFactory(msgPlot, self.newPlot, msgClass, fieldNames)
            if argname == '--send':
                msgname = argvalue
                msgClass = Messaging.MsgClassFromName[msgname]
                if not txMsgs:
                    txMsgs = QtWidgets.QTreeWidget(parent)
                    txMsgs.setColumnCount(4)
                    txMsgsHeader = QtWidgets.QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
                    txMsgs.setHeaderItem(txMsgsHeader)
                    splitter.addWidget(txMsgs)
                
                msg = msgClass()
                # set fields to defaults
                msgWidget = msgtools.lib.txtreewidget.EditableMessageItem(txMsgs, msg)
                msgWidget.qobjectProxy.send_message.connect(self.on_tx_message_send)

        # create a new file
        self.file = None

    def newPlot(self, plot):
        self.plotlayout.addWidget(QtWidgets.QLabel(plot.msgClass.MsgName()))
        self.plotlayout.addWidget(plot)
        if not plot.msgClass.ID in self.msgHandlers:
            self.msgHandlers[plot.msgClass.ID] = []
        self.msgHandlers[plot.msgClass.ID].append(plot)
        
    def on_tx_message_send(self, msg):
        if not self.connected:
            self.OpenConnection()
        self.SendMsg(msg)

    def ProcessMessage(self, msg):
        if msg.ID in self.msgHandlers:
            handlersList = self.msgHandlers[msg.ID]
            for handler in handlersList:
                handler.addData(msg)
        
        if self.file is not None:
            #write to a single binary log file
            self.file.write(msg.hdr.rawBuffer())

            # if you want to write to multiple CSV files, look at lumberjack for an example of how to do so.
            # for each message, you'll need to
            # 1) open a file (store handles to files in a hash based on msg id)
            # 2) look up the MsgNameFromID
            # 3) look up the MsgClassFromName
            # 4) then iterate through the msgClass.fields and msgClass.bitFields
            #  a. to get() the field value as a string for each field, and write them to the file
            # you might also consider using the --msg option to set allowedMessages
            # then you'd get a csv file for each of the messages you care about (and not for the ones you don't)

    def CreateLogFile(self, tag):
        self.CloseLogFile()

        filename = strftime("%Y_%m_%d")
        for lineEdit in self.lineEdits:
            filename += "." + lineEdit.text().replace(" ","_")
        
        if tag is not None:
            filename += "." + tag
        filename += ".log"
        
        # note this opens one binary file to write all the data to.
        self.file = open(filename, 'wb')
        self.statusMsg.setText("Logging to " + filename)

    def CloseLogFile(self):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.statusMsg.setText("NOT Logging")

    def HandleButtonPress(self):
        # when a button is used to start a log, the text of that button changes to "Stop".
        # starting any other log will stop the current one (changing it's text back to normal)
        button = self.sender()
        if button == self.activeLogButton:
            self.CloseLogFile()
            button.setText(button.label)
            self.activeLogButton = None
        else:
            if self.activeLogButton != None:
                self.activeLogButton.setText(self.activeLogButton.label)
            tag = button.tag
            self.CreateLogFile(tag)
            button.setText("Stop")
            self.activeLogButton = button

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = Multilog(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
