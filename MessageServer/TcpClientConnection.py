import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

sys.path.append("../MsgApp")
from Messaging import *

class TcpClientConnection(QObject):
    disconnected = Signal(object)
    messagereceived = Signal(object, object)

    def __init__(self, tcpConnection, msgdir):
        super(TcpClientConnection, self).__init__(None)

        msgLib = Messaging(msgdir, 0)

        self.tcpConnection = tcpConnection
        self.tcpConnection.readyRead.connect(self.onReadyRead)
        self.tcpConnection.disconnected.connect(self.onDisconnected)
        self.tcpConnection.error.connect(self.onError)

        self.rxBuffer = bytearray()

        self.name = "Client " + str(self.tcpConnection.peerAddress())

    @Slot()
    def onReadyRead(self):
        input_stream = QDataStream(self.tcpConnection)

        while(self.tcpConnection.bytesAvailable() > 0):
            # read the header, unless we have the header
            if(len(self.rxBuffer) < Messaging.hdrSize):
                print("reading", Messaging.hdrSize - len(self.rxBuffer), "bytes for header")
                self.rxBuffer += input_stream.readRawData(Messaging.hdrSize - len(self.rxBuffer))
                print("have", len(self.rxBuffer), "bytes")
            
            # if we still don't have the header, break
            if(len(self.rxBuffer) < Messaging.hdrSize):
                print("don't have full header, quitting")
                return
            
            # need to decode body len to read the body
            bodyLen = Messaging.hdr.GetLength(self.rxBuffer)
            
            # read the body, unless we have the body
            if(len(self.rxBuffer) < Messaging.hdrSize + bodyLen):
                print("reading", Messaging.hdrSize + bodyLen - len(self.rxBuffer), "bytes for body")
                self.rxBuffer += input_stream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuffer))
            
            # if we still don't have the body, break
            if(len(self.rxBuffer) < Messaging.hdrSize + bodyLen):
                print("don't have full body, quitting")
                return
            
            # if we got this far, we have a whole message! So, emit the signal
            self.messagereceived.emit(QByteArray(self.rxBuffer), self)

            # then clear the buffer, so we start over on the next message
            self.rxBuffer = ""

    @Slot()
    def onDisconnected(self):
        self.disconnected.emit(self)

    @Slot()
    def onError(self, socketError):
        print(socketError)
