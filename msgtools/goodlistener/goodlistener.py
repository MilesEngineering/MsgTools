#!/usr/bin/env python3
import sys
import queue
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer

from datetime import datetime

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

class MsgTimeoutError(Exception):
    def __init__(self, msgName, timeout):
        self.msgName = msgName
        self.timeout = timeout
    def __str__(self):
        return "Error waiting for " + self.msgName + " after " + str(self.timeout) + " seconds"

class GoodListener(msgtools.lib.gui.Gui):
    MSG_TIMEOUT = 10
    def __init__(self, argv, ThreadClass, parent=None):
        if(len(argv) < 2):
            exit('''
Invoke like this
    ./path/to/GoodListener.py [RESULTS] [LOG]
    
where RESULTS and LOG are the optional results and log files.
''')
        appName = "Good Listener 0.1, " + ThreadClass.__name__
        msgtools.lib.gui.Gui.__init__(self, appName, [argv[0],"file"]+argv[1:], [], parent)
        
        resultsFilename = argv[1]
        logFileName = argv[2]
        
        self.statusWindow = QtWidgets.QPlainTextEdit(self)
        doc = self.statusWindow.document()
        font = doc.defaultFont()
        font.setFamily("Courier New");
        doc.setDefaultFont(font)
        self.setCentralWidget(self.statusWindow)

        self.msgRxList = queue.Queue()
        self.msgTxList = queue.Queue()

        # hook up to received messages
        self.RxMsg.connect(self.ProcessMessage)
        
        self.thread = ThreadClass(self)
        self.thread.status.connect(self.PrintStatus, QtCore.Qt.QueuedConnection)
        self.thread.finished.connect(self.scriptFinished)
        self.thread.start()

        self.txMsgTimer = QTimer(self)
        self.txMsgTimer.setInterval(20) # this is the rate we check for messages to transmit!
        self.txMsgTimer.timeout.connect(self.CheckForTxMsgs)
        self.txMsgTimer.start()

    
    def PrintStatus(self, msg):
        self.statusWindow.appendPlainText(msg)
        #print(msg)
    
    def scriptFinished(self):
        self.statusWindow.appendPlainText(">>> DONE!!")

    # instead of adding a thread and a queue, can we just disable event-based reading from the socket, and have WaitForMsg poll the socket?
    # queue all received messages
    def ProcessMessage(self, msg):
        # create a python object of the message
        self.msgRxList.put(msg)
        #if len(self.msgRxList) > SOME_MAX_VALUE:
        #    raise an error?
    
    def SendMsg(self, msg):
        self.msgTxList.put(msg)
        
    def CheckForTxMsgs(self):
        try:
            while(1):
                msg = self.msgTxList.get(False)
                super(GoodListener, self).SendMsg(msg)
        except queue.Empty:
            pass

    # throw away all queued messages
    def FlushRxQueue(self):
        # http://stackoverflow.com/questions/6517953/clear-all-items-from-the-queue
        with self.msgRxList.mutex:
            self.msgRxList.queue.clear()
    
    # wait for a new message (can include things already in queue!)
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
                msg = self.msgRxList.get(True, remainingTime)
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

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    listener = GoodListener(sys.argv, MyTest)
    listener.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
