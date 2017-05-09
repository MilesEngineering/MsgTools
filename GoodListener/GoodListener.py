#!/usr/bin/env python3
import sys
import queue
import time

from PyQt5 import QtCore, QtGui, QtWidgets

from datetime import datetime

import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append(srcroot+"/MsgApp")
import MsgGui

from Messaging import Messaging

class MsgTimeoutError(Exception):
    def __init__(self, msgName, timeout):
        self.msgName = msgName
        self.timeout = timeout
    def __str__(self):
        return "Error waiting for " + self.msgName + " after " + str(self.timeout) + " seconds"

class GoodListener(MsgGui.MsgGui):
    MSG_TIMEOUT = 10
    def __init__(self, argv, ThreadClass, parent=None):
        if(len(argv) < 2):
            exit('''
Invoke like this
    ./path/to/GoodListener.py [RESULTS] [LOG]
    
where RESULTS and LOG are the optional results and log files.
''')
        
        MsgGui.MsgGui.__init__(self, "Good Listener 0.1", [argv[0],"file"]+argv[1:], [], parent)
        
        resultsFilename = argv[1]
        logFileName = argv[2]
        
        self.statusWindow = QtWidgets.QPlainTextEdit(self)
        self.setCentralWidget(self.statusWindow)

        self.msgList = queue.Queue()

        # hook up to received messages
        self.RxMsg.connect(self.ProcessMessage)
        
        self.thread = ThreadClass(self)
        self.thread.status.connect(self.PrintStatus, QtCore.Qt.QueuedConnection)
        self.thread.finished.connect(self.scriptFinished)
        self.thread.start()
    
    def PrintStatus(self, msg):
        self.statusWindow.appendPlainText(msg)
        #print(msg)
    
    def scriptFinished(self):
        self.statusWindow.appendPlainText(">>> DONE!!")

    # instead of adding a thread and a queue, can we just disable event-based reading from the socket, and have WaitForMsg poll the socket?
    # queue all received messages
    def ProcessMessage(self, msg):
        # create a python object of the message
        self.msgList.put(msg)
        #if len(self.msgList) > SOME_MAX_VALUE:
        #    raise an error?
    
    def WaitForMsg(self, msgName, timeout=None):
        if timeout == None:
            timeout = GoodListener.MSG_TIMEOUT
        try:
            start = datetime.now()
            # need to eventually return None, if no messages arrive!
            for i in range(0, timeout):
                now = datetime.now()
                elapsedTime = (now - start).total_seconds()
                remainingTime = timeout - elapsedTime
                msg = self.msgList.get(True, remainingTime)
                if msg.MsgName() == msgName:
                    return msg
                else:
                    # silently throw away all other queued messages, until we get what we're waiting for?
                    pass
        except queue.Empty:
            raise MsgTimeoutError(msgName, timeout)

class ScriptThread(QtCore.QThread):
    status = QtCore.pyqtSignal(object)
    def __init__(self, listener):
        super(ScriptThread, self).__init__()
        self.listener = listener
    def output(self, msg):
        self.status.emit(msg)

# to use, make a subclass of ScriptThread, and define the following in it:
class MyTest(ScriptThread):
    def __init__(self, listener):
        super(AccelButtonTest, self).__init__(listener)
    def run(self):
        try:
            for i in range (0,3):
                self.output("waiting for msg1")
                msg = self.listener.WaitForMsg('Msg1Name')
                self.output(Messaging.toJson(msg))
                self.output("waiting for msg2")
                msg = self.listener.WaitForMsg('Msg2Name')
                self.output(Messaging.toJson(msg))
        except MsgTimeoutError as e:
            self.output(">>>> " + str(e))

# main starts here
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    listener = GoodListener(sys.argv, MyTest)
    listener.show()
    sys.exit(app.exec_())
