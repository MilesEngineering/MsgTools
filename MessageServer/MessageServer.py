from PySide import QtCore, QtGui, QtNetwork

class MessageServer(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MessageServer, self).__init__(parent)

        statusLabel = QtGui.QLabel()
        quitButton = QtGui.QPushButton("Quit")
        quitButton.setAutoDefault(False)

        self.tcpServer = QtNetwork.QTcpServer(self)
        self.clientList = []

        if not self.tcpServer.listen(port = 5678):
            QtGui.QMessageBox.critical(self, "MessageServer",
                    "Unable to start the server: %s." % self.tcpServer.errorString())
            self.close()
            return

        statusLabel.setText("The server is running on port %d." % self.tcpServer.serverPort())

        quitButton.clicked.connect(self.close)
        self.tcpServer.newConnection.connect(self.handleNewClientConnection)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(quitButton)
        buttonLayout.addStretch(1)

        self.clientListModel = QtGui.QStringListModel(self.clientList)
        self.clientListView = QtGui.QListView()
        self.clientListView.setModel(self.clientListModel)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(statusLabel)
        mainLayout.addWidget(self.clientListView)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle("MessageServer")

    def handleNewClientConnection(self):
        newConnection = self.tcpServer.nextPendingConnection()
        self.clientList.append("Client %d: Port %d" % ( len(self.clientList) + 1, newConnection.peerPort() ))
        self.clientListModel.setStringList(self.clientList)

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
