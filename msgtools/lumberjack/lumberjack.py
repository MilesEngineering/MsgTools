#!/usr/bin/env python3
import sys
import os
import math
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

DESCRIPTION='''
Lumberjack will create a directory named after the input file, and put multiple .csv files (one per message)
in that directory.
'''

EPILOG='''
This utility overrides connectionName with the logfile argument, and forces a "file" connectionType.  This 
disables all socket options, and these will be ignored if specified.
'''

class Lumberjack(msgtools.lib.gui.Gui):
    def __init__(self, parent=None):

        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
        parser.add_argument('logfile', help='''The log file you want to split into CSV.  .log extension 
            assumes the log was created by MsgServer (binary).  A .txt extension assumes the file was
            created by SD logger.''')
        parser=msgtools.lib.gui.Gui.addBaseArguments(parser)
        args = parser.parse_args()

        args.connectionType='file'
        args.connectionName = args.logfile
        if args.logfile.lower().endswith('.txt'):
            args.serial = True
        args.ip = None
        args.port = None
        args.files = []

        msgtools.lib.gui.Gui.__init__(self, "Lumberjack 0.1", args, parent)
        
        self.outputName = self.connectionName.replace('.log', '')
        self.outputName = self.outputName.replace('.txt', '')
        self.outputName = self.outputName.replace('.TXT', '')
        os.makedirs(self.outputName)
        print("outputName is " + self.outputName + "\n")

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)
        
        self.outputFiles = {}

        # to handle timestamp wrapping
        self._timestampOffset = 0
        self._lastTimestamp = 0

        self.messageCount = 0

    def ProcessMessage(self, msg):
        self.messageCount += 1
        
        id = msg.hdr.GetMessageID()

        # if we write CSV to multiple files, we'd probably look up a hash table for this message id,
        # and open it and write a header
        if(id in self.outputFiles):
            outputFile = self.outputFiles[id]
        else:
            # create a new file
            outputFile = open(self.outputName + "/" + msg.MsgName().replace("/","_") + ".csv", 'w')

            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.outputFiles[id] = outputFile
            
            # add table header, one column for each message field
            timeUnits = Messaging.findFieldInfo(msg.hdr.fields, "Time").units
            if timeUnits == "ms":
                timeUnits = "s"
            tableHeader = "Time ("+timeUnits+"), "
            for fieldInfo in type(msg).fields:
                tableHeader += fieldInfo.name + ", "
                for bitInfo in fieldInfo.bitfieldInfo:
                    tableHeader += bitInfo.name + ", "
            tableHeader += '\n'
            outputFile.write(tableHeader)
        
        try:
            # \todo Detect time rolling.  this only matters when we're processing a log file
            # with insufficient timestamp size, such that time rolls over from a large number
            # to a small one, during the log.
            thisTimestamp = msg.hdr.GetTime()
            if thisTimestamp < self._lastTimestamp:
                self._timestampOffset+=1

            self._lastTimestamp = thisTimestamp

            timeSizeInBits = int(round(math.log(int(Messaging.findFieldInfo(msg.hdr.fields, "Time").maxVal), 2)))
            timestamp = (self._timestampOffset << timeSizeInBits) + thisTimestamp
            if Messaging.findFieldInfo(msg.hdr.fields, "Time").units == "ms":
                timestamp = timestamp / 1000.0
            text = str(timestamp) + ", "
        except AttributeError:
            text = "unknown, "

        text += Messaging.toCsv(msg)
        text += '\n'
        outputFile.write(text)

def main():
    app = QtWidgets.QApplication(sys.argv)
    msgApp = Lumberjack()
    msgApp.MessageLoop()
    print("Processed " + str(msgApp.messageCount) + " messages")

# main starts here
if __name__ == '__main__':
    main()
