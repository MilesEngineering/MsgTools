import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

sys.path.append("../MsgApp")

from MsgApp import *

from TcpClientConnection import *

class MessageServer(QObject):
    connectionfailure = Signal()
    newconnectionaccepted = Signal()
    connectiondisconnected = Signal()

    def __init__(self):
        super(MessageServer, self).__init__(None)

        self.connections = {}
        self.tcpServer = QTcpServer()
        self.tcpServer.newConnection.connect(self.onNewConnection)

    def start(self):
        if not self.tcpServer.listen(QHostAddress.Any, 5678):
            self.connectionfailure.emit()
            return

    def onNewConnection(self):
        newConnection = TcpClientConnection(self.tcpServer.nextPendingConnection())
        newConnection.disconnected.connect(self.onConnectionDisconnected)

        self.connections[newConnection] = newConnection
        self.newconnectionaccepted.emit()

    def onConnectionDisconnected(self, connection):
        del self.connections[connection]
        self.connectiondisconnected.emit()