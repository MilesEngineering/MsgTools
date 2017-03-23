#!/usr/bin/env python3
import sys
import uuid

from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from PyQt5.QtCore import QObject

sys.path.append("../MsgApp")
from Messaging import *

class TcpClientConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)

    def __init__(self, tcpSocket):
        super(TcpClientConnection, self).__init__(None)

        self.tcpSocket = tcpSocket
        self.tcpSocket.readyRead.connect(self.onReadyRead)
        self.tcpSocket.disconnected.connect(self.onDisconnected)

        self.rxBuffer = bytearray()

        self.name = "TCP Client " + self.tcpSocket.peerAddress().toString()

    def onReadyRead(self):
        inputStream = QtCore.QDataStream(self.tcpSocket)

        while(self.tcpSocket.bytesAvailable() > 0):
            # read the header, unless we have the header
            if(len(self.rxBuffer) < Messaging.hdrSize):
                self.rxBuffer += inputStream.readRawData(Messaging.hdrSize - len(self.rxBuffer))
            
            # if we still don't have the header, break
            if(len(self.rxBuffer) < Messaging.hdrSize):
                return
            
            # need to decode body len to read the body
            bodyLen = Messaging.hdr.GetDataLength(self.rxBuffer)
            
            # read the body, unless we have the body
            if(len(self.rxBuffer) < Messaging.hdrSize + bodyLen):
                self.rxBuffer += inputStream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuffer))
            
            # if we still don't have the body, break
            if(len(self.rxBuffer) < Messaging.hdrSize + bodyLen):
                return
            
            # if we got this far, we have a whole message! So, emit the signal
            self.messagereceived.emit(self.rxBuffer)

            # then clear the buffer, so we start over on the next message
            self.rxBuffer = bytearray()

    def onDisconnected(self):
        self.disconnected.emit(self)

    def sendMsg(self, msg):
        self.tcpSocket.write(msg)

class TcpServer(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    newConnection = QtCore.pyqtSignal(object)
    connectionDisconnected = QtCore.pyqtSignal(object)

    def __init__(self):
        super(TcpServer, self).__init__(None)

        self.portNumber = 5678
        self.tcpServer = QtNetwork.QTcpServer()
        self.tcpServer.newConnection.connect(self.onNewTcpConnection)

    def start(self):
        if not self.tcpServer.listen(QtNetwork.QHostAddress.Any, self.portNumber):
            self.statusUpdate.emit("Con't open TCP socket on port "+str(self.portNumber)+"!")

    def onNewTcpConnection(self):
        connection = TcpClientConnection(self.tcpServer.nextPendingConnection())

        connection.disconnected.connect(self.onConnectionDisconnected)

        self.newConnection.emit(connection)

    def onConnectionDisconnected(self, connection):
        self.connectionDisconnected.emit(connection)

