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

    def __init__(self, tcpSocket, msgdir):
        super(TcpClientConnection, self).__init__(None)

        msgLib = Messaging(msgdir, 0)

        self.tcpSocket = tcpSocket
        self.tcpSocket.readyRead.connect(self.onReadyRead)
        self.tcpSocket.disconnected.connect(self.onDisconnected)
        self.tcpSocket.error.connect(self.onError)

        self.rxBuffer = bytearray()

        self.name = "Client " + str(self.tcpSocket.peerAddress())

    @Slot()
    def onReadyRead(self):
        inputStream = QDataStream(self.tcpSocket)

        while(self.tcpSocket.bytesAvailable() > 0):
            # read the header, unless we have the header
            if(len(self.rxBuffer) < Messaging.hdrSize):
                print("reading", Messaging.hdrSize - len(self.rxBuffer), "bytes for header")
                self.rxBuffer += inputStream.readRawData(Messaging.hdrSize - len(self.rxBuffer))
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
                self.rxBuffer += inputStream.readRawData(inputStream, Messaging.hdrSize + bodyLen - len(self.rxBuffer))
            
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
