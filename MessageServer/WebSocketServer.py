#!/usr/bin/env python3
import sys

from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork, QtWebSockets
from PyQt5.QtCore import QObject
from PyQt5.QtWebSockets import QWebSocket
from PyQt5.QtWebSockets import QWebSocketServer

sys.path.append("../MsgApp")
from Messaging import *

class WebSocketClientConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)

    def __init__(self, webSocket):
        super(WebSocketClientConnection, self).__init__(None)

        self.webSocket = webSocket
        self.webSocket.binaryMessageReceived.connect(self.processBinaryMessage)
        self.webSocket.disconnected.connect(self.onDisconnected)

        self.name = "Web Client " + self.webSocket.peerAddress().toString()

    def processBinaryMessage(self, message):
        self.messagereceived.emit(message)

    def onDisconnected(self):
        self.disconnected.emit(self)

    def sendMsg(self, msg):
        self.webSocket.sendBinaryMessage(msg)

class WebSocketServer(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    newConnection = QtCore.pyqtSignal(object)
    connectionDisconnected = QtCore.pyqtSignal(object)

    def __init__(self):
        super(WebSocketServer, self).__init__(None)

        self.portNumber = 5679
        self.webSocketServer = QWebSocketServer("MsgServer", QWebSocketServer.NonSecureMode)
        self.webSocketServer.newConnection.connect(self.onNewConnection)

    def start(self):
        if not self.webSocketServer.listen(QtNetwork.QHostAddress.Any, self.portNumber):
            self.statusUpdate.emit("Con't open WebSocket on port "+str(self.portNumber)+"!")

    def onNewConnection(self):
        connection = WebSocketClientConnection(self.webSocketServer.nextPendingConnection())

        connection.disconnected.connect(self.onConnectionDisconnected)

        self.newConnection.emit(connection)

    def onConnectionDisconnected(self, connection):
        self.connectionDisconnected.emit(connection)

