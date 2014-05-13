from PySide import QtCore, QtGui, QtNetwork

class ClientSocket(QtCore.QObject):
    disconnected = QtCore.Signal()

    def __init__(self, tcpSocket):
        super(ClientSocket, self).__init__(None)
        self.tcpSocket = tcpSocket
        self.tcpSocket.readyRead.connect(self.onReadyRead)
        self.tcpSocket.disconnected.connect(self.onDisconnected)

    def onReadyRead(self):
        # Read from socket, emit data (to server)
        # self.emit()
        print("onReadyRead")

    def onDisconnected(self):
        print("onDisconnected")
        self.tcpSocket.deleteLater()
        self.disconnected.emit()


class MessageServer(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MessageServer, self).__init__(parent)

        statusLabel = QtGui.QLabel()
        quitButton = QtGui.QPushButton("Quit")
        quitButton.setAutoDefault(False)

        self.tcpServer = QtNetwork.QTcpServer(self)
        self.clientSockets = []

        if not self.tcpServer.listen(port = 5678):
            QtGui.QMessageBox.critical(self, "MessageServer",
                    "Unable to start the server: %s." % self.tcpServer.errorString())
            self.close()
            return

        statusLabel.setText("The server is running on port %d." % self.tcpServer.serverPort())

        quitButton.clicked.connect(self.close)
        self.tcpServer.newConnection.connect(self.onNewConnection)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(quitButton)
        buttonLayout.addStretch(1)

        self.clientListModel = QtGui.QStringListModel()
        self.clientListView = QtGui.QListView()
        self.clientListView.setModel(self.clientListModel)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(statusLabel)
        mainLayout.addWidget(self.clientListView)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle("MessageServer")

    def onNewConnection(self):
        newClientSocket = ClientSocket(self.tcpServer.nextPendingConnection())

        newClientSocket.disconnected.connect(lambda: self.onDisconnected(newClientSocket))

        self.clientSockets.append(newClientSocket)
        
        self.updateClientListView()

    def onDisconnected(self, newClientSocket):
        self.clientSockets.remove(newClientSocket)
        self.updateClientListView()

    def updateClientListView(self):
        clientsStringList = [];

        for client in self.clientSockets:
            clientsStringList.append("Client %d: Port %d" % ( len(self.clientSockets), client.tcpSocket.peerPort() ))
        
        self.clientListModel.setStringList(clientsStringList)

    def sampleCode(self):
        # clientConnection = self.tcpServer.nextPendingConnection()
        # clientConnection.disconnected.connect(clientConnection.deleteLater)

        # clientConnection.write(block)
        # clientConnection.disconnectFromHost()
        pass

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    server = MessageServer()
    sys.exit(server.exec_())
