#!/usr/bin/env python3
import sys
import os
import math
import argparse
import signal

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui
import msgtools.lib.msgcsv as msgcsv

DESCRIPTION='''
    Lumberjack creates a subdirectory, and one CSV file per message type received in that directory.
    You may source data from any connectionType.  If you specify a logfile name positional
    Lumberjack assumes you want to source from a logfile.
'''
class Lumberjack(msgtools.lib.gui.Gui):
    def __init__(self, parent=None):

        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('-o', '--outputdir', help='''Specifies the name of the directory to output
            parsed data to.  Required for non-file connectionTypes.''')
        parser.add_argument('logfile', nargs='?', default=None, help='''The log file you want to split into CSV.  
            .log extension assumes the log was created by MsgServer (binary).  A .txt extension assumes the 
            file was created by SD logger.  This option is a pseudonym for --connectionType='file' and 
            --connectionName=<filename>, and will override connectionType, and connectionName.''')
        parser=msgtools.lib.gui.Gui.addBaseArguments(parser)
        args = parser.parse_args()

        # Special Handling here for files...
        if args.logfile is not None:
            args.connectionType = 'file'
            args.connectionName = args.logfile
            if args.logfile.lower().endswith('.txt'):
                args.serial = True
            args.ip = None
            args.port = None


        msgtools.lib.gui.Gui.__init__(self, "Lumberjack 0.1", args, parent)
        
        # If the user specified the output dir use it.  If the user 
        # specified a source file
        if args.outputdir is not None:
            self.outputName = args.outputdir
        elif args.connectionType == 'file':
            if args.connectionName is not None:
                self.outputName = self.connectionName.replace('.log', '')
                self.outputName = self.outputName.replace('.txt', '')
                self.outputName = self.outputName.replace('.TXT', '')
            else:
                print('''You must specify the name of the source file in --connectionName
                    of logfile for a \'file\' connectionType.''')
                sys.exit(1)
        else:
            print('You must specify the -o option if you aren\'t using a \'file\' connectionType')
            sys.exit(1)

        if os.path.exists(self.outputName) is False:
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

        text += msgcsv.toCsv(msg)
        text += '\n'
        outputFile.write(text)

        # This is not efficient, but if we don't flush during socket processing
        # and the user hits Ctrl-C, we'll drop a bunch of data and end up with empty files.
        # So flush each message as it comes in.
        if self.connectionType !='file':
            outputFile.flush()

def main():
    app = QtWidgets.QApplication(sys.argv)
    msgApp = Lumberjack()

    # If we are processing a file then  use the Message Loop.  The reason for this dichotomy
    # in processing is the sockets are QtTcpSockets.  We've tied into Qt signals, which require
    # the app event loop to be running.  Files are handled with straight up Python files.

    # I can think of several other approaches, but they all pretty much boil down to sticking 
    # with QtApplication's event loop and going full on Qt, or kicking off a background worker 
    # thread and using Qt waitFor* constructs or straight up Python.

    # For now this little band-aid will get us by
    if msgApp.connectionType != 'file':
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        print('Listening for messages.  Press Ctrl-C to exit.')
        app.exec_()
    else:
        msgApp.MessageLoop()

    print("Processed " + str(msgApp.messageCount) + " messages")

# main starts here
if __name__ == '__main__':
    main()
