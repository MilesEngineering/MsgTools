from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork, QtWebSockets
from PyQt5.QtCore import QObject
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWebSockets import QWebSocketServer

from msgtools.lib.messaging import Messaging

class WebSocketClientConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)

    def __init__(self, webSocket):
        super(WebSocketClientConnection, self).__init__(None)

        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(lambda: self.webSocket.close())
        self.statusLabel = QtWidgets.QLabel()
        self.subscriptions = {}
        self.subMask = ~0
        self.subValue = 0
        self.isHardwareLink = False

        self.webSocket = webSocket
        self.webSocket.binaryMessageReceived.connect(self.processBinaryMessage)
        self.webSocket.disconnected.connect(self.onDisconnected)

        self.name = "Web Client " + self.webSocket.peerAddress().toString()
        self.statusLabel.setText(self.name)

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.statusLabel
        return None
            
    def processBinaryMessage(self, bytes):
        hdr = Messaging.hdr(bytes.data())
        self.messagereceived.emit(hdr)

    def onDisconnected(self):
        self.disconnected.emit(self)

    def sendMsg(self, msg):
        self.webSocket.sendBinaryMessage(msg.rawBuffer().raw)

class WebSocketServer(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    newConnection = QtCore.pyqtSignal(object)

    def __init__(self, portNumber):
        super(WebSocketServer, self).__init__(None)

        self.portNumber = portNumber
        self.webSocketServer = QWebSocketServer("MsgServer", QWebSocketServer.NonSecureMode)
        self.webSocketServer.newConnection.connect(self.onNewConnection)

    def start(self):
        if not self.webSocketServer.listen(QtNetwork.QHostAddress.Any, self.portNumber):
            self.statusUpdate.emit("Con't open WebSocket on port "+str(self.portNumber)+"!")

    def onNewConnection(self):
        connection = WebSocketClientConnection(self.webSocketServer.nextPendingConnection())
        self.newConnection.emit(connection)
