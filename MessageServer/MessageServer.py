#!/usr/bin/env python3
import sys
import os
import getopt

srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.append(srcroot+"/MsgApp")

from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork

from TcpServer import *
from WebSocketServer import *

from Messaging import Messaging

class MessageServer(QtWidgets.QMainWindow):
    def __init__(self, argv):
        QtWidgets.QMainWindow.__init__(self)
        
        srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
        msgdir = srcroot+"/../obj/CodeGenerator/Python/"
        self.msgLib = Messaging(msgdir, 0, "NetworkHeader")
        self.connectClass = Messaging.MsgClassFromName["Network.Connect"]
        self.subscriptionListClass = Messaging.MsgClassFromName["Network.SubscriptionList"]
        self.maskedSubscriptionClass = Messaging.MsgClassFromName["Network.MaskedSubscription"]

        self.clients = {}

        self.initializeGui()

        self.tcpServer = TcpServer()
        self.tcpServer.statusUpdate.connect(self.onStatusUpdate)
        self.tcpServer.newConnection.connect(self.onNewConnection)

        self.wsServer = WebSocketServer()
        self.wsServer.statusUpdate.connect(self.onStatusUpdate)
        self.wsServer.newConnection.connect(self.onNewConnection)

        options = ['serial=', 'bluetooth=']
        self.optlist, args = getopt.getopt(sys.argv[1:], '', options)
        for opt in self.optlist:
            if opt[0] == '--serial':
                from SerialPlugin import SerialConnection
                serialPortName = opt[1]
                self.serialPort = SerialConnection(serialPortName)
                self.serialPort.statusUpdate.connect(self.onStatusUpdate)
                self.onNewConnection(self.serialPort)
                self.serialPort.start()
            elif opt[0] == '--bluetooth':
                from BluetoothPlugin import BluetoothConnection
                bluetoothPortName = opt[1]
                self.bluetoothPort = BluetoothConnection(bluetoothPortName)
                self.bluetoothPort.statusUpdate.connect(self.onStatusUpdate)
                self.onNewConnection(self.bluetoothPort)
                self.bluetoothPort.start()

        self.tcpServer.start()
        self.wsServer.start()
        name = self.tcpServer.serverInfo() + "(TCP) and " + str(self.wsServer.portNumber) + "(WebSocket)"
        self.statusBar().addPermanentWidget(QtWidgets.QLabel(name))

    def initializeGui(self):

        # Components
        self.statusBox = QtWidgets.QPlainTextEdit()

        # Layout
        vbox = QtWidgets.QVBoxLayout()
        self.grid = QtWidgets.QGridLayout()
        vbox.addLayout(self.grid)
        vbox.addWidget(self.statusBox)

        # Central Widget (QMainWindow limitation)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)

        # Main Window Stuff
        self.setWindowTitle("MessageServer 0.1")
        self.setGeometry(300, 100, 800, 400)
        self.statusBar()

    def onStatusUpdate(self, message):
        #self.statusBar().showMessage(message)
        self.statusBox.appendPlainText(message)

    def onNewConnection(self, newConnection):
        self.onStatusUpdate("adding connection[" + newConnection.name+"]")
        self.clients[newConnection] = newConnection
        newConnection.messagereceived.connect(self.onMessageReceived)
        newConnection.disconnected.connect(self.onConnectionDied)
        clientRow = self.grid.rowCount()
        i = 0
        while(1):
            widget = newConnection.widget(i)
            if widget == None:
                break
            self.grid.addWidget(widget, clientRow, i)
            i+=1

    def onConnectionDied(self, connection):
        self.onStatusUpdate("removing connection[" + connection.name+"]")
        i = 0
        while(1):
            widget = connection.widget(i)
            if widget == None:
                break
            self.grid.removeWidget(widget)
            widget.deleteLater()
            i+=1
        if connection in self.clients:
            connection.deleteLater()
            del self.clients[connection]
        else:
            self.onStatusUpdate("cnx not in list!")

    def onMessageReceived(self, message):
        clientThatReceivedMsg = self.sender()
        # check for name, subscription, etc.
        if Messaging.hdr.GetMessageID(message) == self.connectClass.ID:
            clientThatReceivedMsg.name = self.connectClass.GetName(message)
            clientThatReceivedMsg.statusLabel.setText(clientThatReceivedMsg.name)
        elif Messaging.hdr.GetMessageID(message) == self.subscriptionListClass.ID:
            pass
        elif Messaging.hdr.GetMessageID(message) == self.maskedSubscriptionClass.ID:
            pass
        for client in self.clients.values():
            if client != clientThatReceivedMsg:
                client.sendMsg(message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    msgServer = MessageServer(sys.argv)
    msgServer.show()

    sys.exit(app.exec_())
