#!/usr/bin/env python3
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class Lumberjack(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "Message Inspector 0.1", [argv[0],"file"]+argv[1:], parent)
        
        self.outputName = self.connectionName.replace('.log', '')
        self.outputName = self.connectionName.replace('.txt', '')
        os.makedirs(self.outputName)
        print("outputName is " + self.outputName + "\n")

        # event-based way of getting messages
        self.RxMsg.connect(self.PrintMessage)
        
        self.outputFiles = {}


    def PrintMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        id       = hex(Messaging.hdr.GetID(msg))
        msgName = Messaging.MsgNameFromID[id]
        msgClass = Messaging.MsgClassFromName[msgName]

        if(msgClass == None):
            print("WARNING!  No definition for ", id, "!\n")
            return

        # if we write CSV to multiple files, we'd probably look up a hash table for this message id,
        # and open it and write a header
        if(id in self.outputFiles):
            outputFile = self.outputFiles[id]
        else:
            # create a new file
            outputFile = open(self.outputName + "/" + msgName + ".csv", 'w')

            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.outputFiles[id] = outputFile
            
            # add table header, one column for each message field
            tableHeader = "Time (ms), "
            for fieldInfo in msgClass.fields:
                tableHeader += fieldInfo.name + ", "
                for bitInfo in fieldInfo.bitfieldInfo:
                    tableHeader += bitInfo.name + ", "
            tableHeader += '\n'
            outputFile.write(tableHeader)
        
        try:
            text = str(Messaging.hdr.GetTime(msg)) + ", "
        except AttributeError:
            text = "unknown, "

        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                columnText = str(Messaging.get(msg, fieldInfo)) + ", "
                for bitInfo in fieldInfo.bitfieldInfo:
                    columnText += str(Messaging.get(msg, bitInfo)) + ", "
            else:
                columnText = ""
                for i in range(0,fieldInfo.count):
                    columnText += str(Messaging.get(msg, fieldInfo, i)) + ", "
            text += columnText
        text += '\n'
        outputFile.write(text)

# main starts here
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    msgApp = Lumberjack(sys.argv)
    msgApp.MessageLoop()
