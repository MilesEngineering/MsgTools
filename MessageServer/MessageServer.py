#!/usr/bin/env python3
import sys
import os
import getopt

srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.append(srcroot+"/MsgApp")

from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork

from TcpServer import *
from ConnectionsTableModel import *
from WebSocketServer import *

from Messaging import Messaging

class MessageServer(QtWidgets.QMainWindow):
    def __init__(self, argv):
        QtWidgets.QMainWindow.__init__(self)
        
        srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
        msgdir = srcroot+"/../obj/CodeGenerator/Python/"
        self.msgLib = Messaging(msgdir, 0, "NetworkHeader")

        self.clients = {}

        self.initializeGui()

        self.tcpServer = TcpServer()
        self.tcpServer.statusUpdate.connect(self.onStatusUpdate)
        self.tcpServer.newConnection.connect(self.onNewConnection)
        self.tcpServer.connectionDisconnected.connect(self.onConnectionDied)

        self.wsServer = WebSocketServer()
        self.wsServer.statusUpdate.connect(self.onStatusUpdate)
        self.wsServer.newConnection.connect(self.onNewConnection)
        self.wsServer.connectionDisconnected.connect(self.onConnectionDied)

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

    def initializeGui(self):

        # Components
        self.connectionsModel = ConnectionsTableModel(self.clients)
        self.connectionsTable = QtWidgets.QTableView()
        self.connectionsTable.setModel(self.connectionsModel)

        # Layout
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.connectionsTable, 0, 0)

        # Central Widget (QMainWindow limitation)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

        # Main Window Stuff
        self.setWindowTitle("MessageServer 0.1")
        self.setGeometry(300, 100, 800, 400)
        self.statusBar()

    def onStatusUpdate(self, message):
        self.statusBar().showMessage(message)

    def onNewConnection(self, newConnection):
        self.clients[newConnection] = newConnection
        newConnection.messagereceived.connect(self.onMessageReceived)
        # Just let the AbstractTableModel know data has changed so that the table view will re-render
        self.connectionsModel.refresh()

    def onConnectionDied(self, connection):
        del self.clients[connection]
        self.connectionsModel.refresh()

    def onMessageReceived(self, message):
        clientThatReceivedMsg = self.sender()
        for client in self.clients.values():
            if client != clientThatReceivedMsg:
                client.sendMsg(message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    msgServer = MessageServer(sys.argv)
    msgServer.show()

    sys.exit(app.exec_())
