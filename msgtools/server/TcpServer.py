from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from PyQt5.QtCore import QObject

from msgtools.lib.messaging import Messaging

class TcpClientConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)

    def __init__(self, tcpSocket):
        super(TcpClientConnection, self).__init__(None)

        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(lambda: self.tcpSocket.close())
        self.statusLabel = QtWidgets.QLabel()
        self.subscriptions = {}
        self.subMask = ~0
        self.subValue = 0
        self.isHardwareLink = False
        
        self.tcpSocket = tcpSocket
        self.tcpSocket.readyRead.connect(self.onReadyRead)
        self.tcpSocket.disconnected.connect(self.onDisconnected)

        self.rxBuffer = bytearray()

        self.name = "TCP Client"
        self.hostLabel = QtWidgets.QLabel(self.tcpSocket.peerAddress().toString().replace("::ffff:",""))
        self.statusLabel.setText(self.name)

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.statusLabel
        if index == 2:
            return self.hostLabel
        return None
            
    def onReadyRead(self):
        inputStream = QtCore.QDataStream(self.tcpSocket)

        while(1):
            if len(self.rxBuffer) < Messaging.hdrSize:
                if self.tcpSocket.bytesAvailable() < Messaging.hdrSize:
                    return
                self.rxBuffer += inputStream.readRawData(Messaging.hdrSize - len(self.rxBuffer))

            if len(self.rxBuffer) >= Messaging.hdrSize:
                hdr = Messaging.hdr(self.rxBuffer)
                bodyLen = hdr.GetDataLength()
                if len(self.rxBuffer)+self.tcpSocket.bytesAvailable() < Messaging.hdrSize + bodyLen:
                    return

                self.rxBuffer += inputStream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuffer))

                # create a new header object with the appended body
                hdr = Messaging.hdr(self.rxBuffer)

                # if we got this far, we have a whole message! So, emit the signal
                self.messagereceived.emit(hdr)

                # then clear the buffer, so we start over on the next message
                self.rxBuffer = bytearray()

    def onDisconnected(self):
        self.disconnected.emit(self)

    def sendMsg(self, msg):
        buf = msg.rawBuffer().raw
        while len(buf) > 0:
            bytesWritten = self.tcpSocket.write(buf)
            if bytesWritten == -1:
                raise Exception('Write error (-1)')
            buf = buf[bytesWritten:]
    
class TcpServer(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    newConnection = QtCore.pyqtSignal(object)

    def __init__(self, portNumber):
        super(TcpServer, self).__init__(None)

        self.portNumber = portNumber
        self.tcpServer = QtNetwork.QTcpServer()
        self.tcpServer.newConnection.connect(self.onNewTcpConnection)

    def start(self):
        if not self.tcpServer.listen(QtNetwork.QHostAddress.Any, self.portNumber):
            self.statusUpdate.emit("Con't open TCP socket on port "+str(self.portNumber)+"!")

    def onNewTcpConnection(self):
        connection = TcpClientConnection(self.tcpServer.nextPendingConnection())
        self.newConnection.emit(connection)
        connection.statusUpdate.connect(self.clientStatusUpdate)

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

    def clientStatusUpdate(self, msg):
        self.statusUpdate.emit(msg)