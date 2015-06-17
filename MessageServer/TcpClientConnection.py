import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

class TcpClientConnection(QObject):
    disconnected = Signal(object)

    def __init__(self, tcpConnection):
        super(TcpClientConnection, self).__init__(None)

        self.tcpConnection = tcpConnection
        self.tcpConnection.readyRead.connect(self.onReadyRead)
        self.tcpConnection.disconnected.connect(self.onDisconnected)
        self.tcpConnection.error.connect(self.onError)

        self.name = "Client " + str(self.tcpConnection.peerAddress())

    @Slot()
    def onReadyRead(self):
        # print(self.tcpConnection.readAll())
        pass

    @Slot()
    def onDisconnected(self):
        self.disconnected.emit(self)

    @Slot()
    def onError(self, socketError):
        print(socketError)
