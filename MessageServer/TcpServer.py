from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from PyQt5.QtCore import QObject

from Messaging import *

class TcpClientConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)

    def __init__(self, tcpSocket):
        super(TcpClientConnection, self).__init__(None)

        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(lambda: self.tcpSocket.close())
        self.statusLabel = QtWidgets.QLabel()
        
        self.tcpSocket = tcpSocket
        self.tcpSocket.readyRead.connect(self.onReadyRead)
        self.tcpSocket.disconnected.connect(self.onDisconnected)

        self.rxBuffer = bytearray()

        self.name = "TCP Client " + self.tcpSocket.peerAddress().toString()
        self.statusLabel.setText(self.name)

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.statusLabel
        return None
            
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
        self.newConnection.emit(connection)

    def serverInfo(self):
        # Show IP address and port number in status bar
        name = ""
        for address in QtNetwork.QNetworkInterface.allAddresses():
            if address.protocol() == QtNetwork.QAbstractSocket.IPv4Protocol and address != QtNetwork.QHostAddress.LocalHost:
                addrStr = address.toString()
                # ignore VM/VPN stuff (special ubuntu address, and anything that ends in 1)
                if ".".split(addrStr)[-1] != "1" and addrStr != "192.168.122.1":
                    name += address.toString() + "/"
        name = name[:-1]
        name += " : " + str(self.portNumber)
        return name
