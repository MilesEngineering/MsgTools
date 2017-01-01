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
        if(len(argv) < 2):
            exit('''
Invoke like this
    ./path/to/Lumberjack.py FILENAME
    
where FILENAME is the name of the log file you'd like to split into CSV.

If the file extension is .bin it will be assumed to be a og file created by MessageServer,
if the file extension is .txt it will be assumed to be a log file created by the SparkFun serial SD logger.
Lumberjack will create a directory named after the input file, and put multiple .csv files (one per message)
in that directory.''')
        
        MsgGui.MsgGui.__init__(self, "Message Inspector 0.1", [argv[0],"file"]+argv[1:], [], parent)
        
        self.outputName = self.connectionName.replace('.log', '')
        self.outputName = self.outputName.replace('.txt', '')
        self.outputName = self.outputName.replace('.TXT', '')
        os.makedirs(self.outputName)
        print("outputName is " + self.outputName + "\n")

        # event-based way of getting messages
        self.RxMsg.connect(self.PrintMessage)
        
        self.outputFiles = {}

        # to handle timestamp wrapping
        self._timestampOffset = 0
        self._lastTimestamp = 0

    def PrintMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        id       = hex(Messaging.hdr.GetMessageID(msg))
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
            outputFile = open(self.outputName + "/" + msgName.replace("/","_") + ".csv", 'w')

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
            # \todo Detect time rolling.  this only matters when we're processing a log file
            # with insufficient timestamp size, such that time rolls over from a large number
            # to a small one, during the log.
            thisTimestamp = Messaging.hdr.GetTime(msg)
            if thisTimestamp < self._lastTimestamp:
                self._timestampOffset+=1

            self._lastTimestamp = thisTimestamp

            text = str((self._timestampOffset << 16) + thisTimestamp) + ", "
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
