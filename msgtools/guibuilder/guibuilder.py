#!/usr/bin/env python3

# TODO
#   add hotkey support (already reading options for it on cmdline)
#  Add annotation field.
#         text gets inserted in log whenever you hit enter in annotation box or click 'note' button next to annotate box.

import os
import sys
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
from time import strftime

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
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
    individual basis, and send and receive messages.  Pressing a button 
    starts/stops a log file.  Underscores in label or field are replaced 
    with spaces for display (to make entering command-line args easier)

    Log filenames will be composed like so:
        YEAR_MONTH_DAY.TEXT1.TEXT2.TAG1.log'''

EPILOG='''
    Example usage: multilog --note LABEL1 LABEL2 --button hotkey:X logtag:TAG1 label:LABEL3  
    --button hotkey:X logtag:TAG2 label:LABEL4 --show MSGNAME MSGNAME2 --plot MSGNAME=fieldname1,fieldname2
    MSGNAME2=fieldname3,fieldname4 --send MSGNAME MSGNAME2
    '''

def removePrefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text

help = '''
    --note: each --note argument adds a text field named the specified LABEL, and 
               the value of the text field will become part of the filename.  
               Example argument: LABEL1
    --button: each --button argument adds a pushbutton named for the specified LABEL, with a 
                hotkey of the specified key.  If logtag value is specified, a button press
                will start/stop logging, and the logtag will become part of the filename.
                If a send value is specified, a button press will send messages.
                Example argument: hotkey:X,logtag:TAG1,label:LABEL1
    --show: each --show argument adds a table view of that MSGNAME
    --row: switch to a row for active layout
    --endrow: end the current row of active layout
    --col: switch to a column for active layout
    --endcol: end the current column of active layout
    --plot: each --plot argument adds a plot of the fields within MSGNAME.  If fields left off, all 
                fields are plotted.  Add [idx] to field name if array and want element
                other than element zero.  Example argument: MSGNAME=fieldname1,fieldname2[2]
    --send:each --send argument is a message name that adds a tree view to edit a message with a 'send' 
                button to send it.  Example argument: MSGNAME
'''

local_args = {"--note":True, "--button": True, "--show":True, "--plot":True, "--send": True, "--tab": True, "--endtab": True, "--log": True,
              "--row": True, "--endrow": True, "--col": True, "--endcol": True}
def base_args(argv):
    ret = []
    ignore = False
    for arg in argv:
        if ignore:
            if arg.startswith('--'):
                ignore = (arg in local_args) or (arg.startswith("--log="))
        else:
            ignore = (arg in local_args) or (arg.startswith("--log="))
        if not ignore:
            ret.append(arg)
    return ret
    
class Multilog(msgtools.lib.gui.Gui):
    def __init__(self, argv, parent=None):
        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)

        parser = msgtools.lib.gui.Gui.addBaseArguments(parser)

        bargs = base_args(argv[1:])
        args=parser.parse_args(bargs)

        msgtools.lib.gui.Gui.__init__(self, "Multilog 0.1", args, parent)
        self.logFileType = 'csv' # default to CSV
        
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)
        
        # handling of messages by sub-widgets
        self.msgHandlers = {}

        # Top level layout
        widget = QtWidgets.QWidget(self)
        mainLayout = QtWidgets.QVBoxLayout(widget)
        self.setCentralWidget(widget)
        self.statusMsg = QtWidgets.QLabel("NOT logging")
        mainLayout.addWidget(self.statusMsg)
        self.tabs = None

        # Layout stack handling
        self.layoutStack = []
        self.activeLayout = None
        mainLayout.type = 'main'
        self.pushLayout(mainLayout)
        
        self.hotKeys = []
        self.noteFields = []
        self.buttons = []
        self.activeLogButton = None
        txMsgs = None
        firstPlot = None

        # Process command line args
        for i in range(1, len(argv)):
            argname = argv[i]

            argvalue = []
            i+=1
            while(1):
                if i >= len(argv) or argv[i].startswith("--"):
                    break
                argvalue.append(argv[i])
                i+=1
            if argname == '--note':
                hLayout = QtWidgets.QHBoxLayout()
                leftvLayout = QtWidgets.QVBoxLayout()
                rightvLayout = QtWidgets.QVBoxLayout()
                hLayout.addLayout(leftvLayout)
                hLayout.addLayout(rightvLayout)
                self.activeLayout.addLayout(hLayout)
                for field in argvalue:
                    label = field.replace("_", " ")

                    # add text field
                    leftvLayout.addWidget(QtWidgets.QLabel(label))
                    noteField = QtWidgets.QLineEdit()
                    rightvLayout.addWidget(noteField)
                    self.noteFields.append(noteField)
            elif argname == '--button':
                options = {}
                for option in argvalue:
                    key, value = option.split(":")
                    if key in options:
                        options[key].append(value)
                    else:
                        options[key] = [value]

                # add button
                label = options["label"][0].replace("_", " ")
                button = QtWidgets.QPushButton(label)
                button.options = options
                # how to set hot key?  do it at window level, or at button level?  or something else?
                if 'hotkey' in options:
                    hotKey = options["hotkey"][0]
                    self.hotKeys[hotKey] = button
                button.label = label
                self.buttons.append(button)
                self.activeLayout.addWidget(button)
                
                button.clicked.connect(self.HandleButtonPress)

            elif argname == '--show':
                for msgname in argvalue:
                    subLayout = QtWidgets.QVBoxLayout()
                    self.activeLayout.addLayout(subLayout)
                    subLayout.addWidget(QtWidgets.QLabel(msgname))
                    msgClass = Messaging.MsgClassFromName[msgname]
                    msgWidget = msgtools.lib.gui.MsgTextWidget(msgClass)
                    subLayout.addWidget(msgWidget)
                    if not msgClass.ID in self.msgHandlers:
                        self.msgHandlers[msgClass.ID] = []
                    self.msgHandlers[msgClass.ID].append(msgWidget)

            elif argname == '--plot':
                if plottingLoaded:
                    for plotarg in argvalue:
                        if "=" in plotarg:
                            split = plotarg.split("=")
                            msgname = split[0]
                            fieldNames = split[1].split(',')
                        else:
                            msgname = plotarg
                            fieldNames = []
                        msgClass = Messaging.MsgClassFromName[msgname]
                        msgPlot = None
                        if firstPlot:
                            MsgPlot.plotFactory(self.newPlot, msgClass, fieldNames, **plotargs)
                        else:
                            firstPlot = MsgPlot.plotFactory(self.newPlot, msgClass, fieldNames, displayControls=False)
                            plotargs = {"runButton":firstPlot.runButton, "clearButton":firstPlot.clearButton, "timeSlider":firstPlot.timeSlider, "displayControls":False}

            elif argname == '--send':
                for msgname in argvalue:
                    msgClass = Messaging.MsgClassFromName[msgname]
                    if not txMsgs:
                        txMsgs = QtWidgets.QTreeWidget(parent)
                        txMsgs.setColumnCount(4)
                        txMsgsHeader = QtWidgets.QTreeWidgetItem(None, ["Message", "Field", "Value", "Units", "Description"])
                        txMsgs.setHeaderItem(txMsgsHeader)
                        self.activeLayout.addWidget(txMsgs)
                    
                    msg = msgClass()
                    # set fields to defaults
                    msgWidget = msgtools.lib.txtreewidget.EditableMessageItem(txMsgs, msg)
                    msgWidget.qobjectProxy.send_message.connect(self.on_tx_message_send)
            elif argname == '--row':
                l = QtWidgets.QHBoxLayout()
                l.type = 'row'
                self.activeLayout.addLayout(l)
                self.pushLayout(l)
            elif argname == '--col':
                l = QtWidgets.QVBoxLayout()
                l.type = 'col'
                self.activeLayout.addLayout(l)
                self.pushLayout(l)
            elif argname == '--tab':
                self.addTab(argvalue[0])
            elif argname == '--endrow':
                self.popLayout('row')
            elif argname == '--endcol':
                self.popLayout('col')
            elif argname == '--endtab':
                self.popLayout('tab')
            elif argname == '--log':
                self.logFileType = argvalue[0]
            elif argname.startswith('--log='):
                self.logFileType = argname.split("=")[1]

        if firstPlot:
            hLayout = QtWidgets.QHBoxLayout()
            mainLayout.addLayout(hLayout)
            hLayout.addWidget(firstPlot.runButton)
            hLayout.addWidget(firstPlot.clearButton)
            hLayout.addWidget(QtWidgets.QLabel("Time Scale"))
            hLayout.addWidget(firstPlot.timeSlider)

    def printLayout(self, prefix):
        layouts = prefix
        for l in self.layoutStack:
            layouts += " " + l.type
        print(layouts)

    def pushLayout(self, newLayout):
        self.layoutStack.append(newLayout)
        self.activeLayout = newLayout
        #self.printLayout('+')
    
    def popLayout(self, layoutType):
        #self.printLayout('-')
        found_it = False
        while len(self.layoutStack) > 1:
            p = self.layoutStack.pop()
            self.activeLayout = self.layoutStack[-1]
            if p.type == layoutType:
                found_it = True
                break
        if not found_it:
            print("Warning: Trying to remove layout %s, couldn't find it!" % layoutType)

    def addTab(self, name):
        if self.tabs == None:
            self.tabs = QtWidgets.QTabWidget()
            self.activeLayout.addWidget(self.tabs)
        tabWidget = QtWidgets.QWidget()
        self.tabs.addTab(tabWidget, name)
        vLayout = QtWidgets.QVBoxLayout()
        tabWidget.setLayout(vLayout)
        vLayout.type = 'tab'
        self.pushLayout(vLayout)

    def newPlot(self, plot):
        vLayout = QtWidgets.QVBoxLayout()
        vLayout.addWidget(QtWidgets.QLabel(plot.msgClass.MsgName()))
        vLayout.addWidget(plot)
        self.activeLayout.addLayout(vLayout)
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
        
        self.logMsg(msg)

    def CreateLogFile(self, tag):
        self.CloseLogFile()

        currentDateTime = QtCore.QDateTime.currentDateTime()
        filename = currentDateTime.toString("yyyyMMdd-hhmmss")

        for noteField in self.noteFields:
            filename += "." + noteField.text().replace(" ", "_")
        
        if tag:
            filename += "." + tag
        filename +=  "." + self.logFileType
        
        self.startLog(filename)
        self.statusMsg.setText("Logging to " + filename)

    def CloseLogFile(self):
        self.stopLog()
        self.statusMsg.setText("NOT Logging")

    def HandleButtonPress(self):
        # when a button is used to start a log, the text of that button changes to "Stop".
        # starting any other log will stop the current one (changing it's text back to normal)
        button = self.sender()
        if "logtag" in button.options:
            if button == self.activeLogButton:
                self.CloseLogFile()
                button.setText(button.label)
                self.activeLogButton = None
            else:
                if self.activeLogButton != None:
                    self.activeLogButton.setText(self.activeLogButton.label)
                self.CreateLogFile(button.options["logtag"][0])
                button.setText("Stop")
                self.activeLogButton = button
        if "send" in button.options:
            for opts in button.options['send']:
                msgname = opts.split("[")[0]
                fields = opts.split("[")[1].replace("]","").split(",")
                msgClass = Messaging.MsgClassFromName[msgname]
                msg = msgClass()
                for field in fields:
                    parts = field.split("=")
                    name = parts[0]
                    value = parts[1]
                    Messaging.set(msg, Messaging.findFieldInfo(msgClass.fields, name), value)
                self.SendMsg(msg)

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = Multilog(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
