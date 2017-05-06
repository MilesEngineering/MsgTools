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
        
        self.settings = QtCore.QSettings("MsgTools", "MessageServer")
        self.logFile = None
        
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

        options = ['serial=', 'bluetoothSPP=', 'plugin=']
        self.optlist, args = getopt.getopt(sys.argv[1:], '', options)
        for opt in self.optlist:
            if opt[0] == '--serial':
                from SerialHeader import SerialHeader
                from SerialPlugin import SerialConnection
                serialPortName = opt[1]
                self.serialPort = SerialConnection(SerialHeader, serialPortName)
                self.serialPort.statusUpdate.connect(self.onStatusUpdate)
                self.onNewConnection(self.serialPort)
                self.serialPort.start()
            elif opt[0] == '--bluetoothSPP':
                from BluetoothHeader import BluetoothHeader
                from SerialPlugin import SerialConnection
                bluetoothPortName = opt[1]
                self.bluetoothPort = SerialConnection(BluetoothHeader, bluetoothPortName)
                self.bluetoothPort.statusUpdate.connect(self.onStatusUpdate)
                self.onNewConnection(self.bluetoothPort)
                self.bluetoothPort.start()
            elif opt[0] == '--plugin':
                filename = opt[1]
                moduleName = os.path.splitext(os.path.basename(filename))[0]
                if Messaging.debug:
                    print("loading module ", filename, "as",moduleName)
                self.plugin = imp.load_source(filename.replace("/", "_"), filename)

                self.pluginPort = self.plugin.PluginConnection()
                self.pluginPort.statusUpdate.connect(self.onStatusUpdate)
                self.pluginPort.newConnection.connect(self.onNewConnection)
                self.pluginPort.start()

        self.tcpServer.start()
        self.wsServer.start()
        name = self.tcpServer.serverInfo() + "(TCP) and " + str(self.wsServer.portNumber) + "(WebSocket)"
        self.statusBar().addPermanentWidget(QtWidgets.QLabel(name))

    def initializeGui(self):
        # Layout
        vbox = QtWidgets.QVBoxLayout()
        self.grid = QtWidgets.QGridLayout()
        vbox.addLayout(self.grid)

        # Components
        self.logButton = QtWidgets.QPushButton("Start Logging")
        self.logButton.pressed.connect(self.onLogButtonClicked)
        vbox.addWidget(self.logButton)

        self.statusBox = QtWidgets.QPlainTextEdit()
        vbox.addWidget(self.statusBox)

        # Central Widget (QMainWindow limitation)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)

        # Main Window Stuff
        self.setWindowTitle("MessageServer 0.1")
        self.setGeometry(300, 100, 800, 400)
        self.statusBar()
    
    def onLogButtonClicked(self):
        if self.logFile != None:
            self.logFile.close()
            self.logFile = None
            self.logButton.setText("Start Logging")
        else:
            currentDateTime = QtCore.QDateTime.currentDateTime()
            defaultFilename = currentDateTime.toString("yyyyMMdd-hhmmss") + ".log"
            logFileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", self.settings.value("logging/filename", ".")+"/"+defaultFilename, "Log Files (*.log)")
            # if they hit cancel, don't do anything
            if not logFileName:
                return
            self.logFile = QtCore.QFile(logFileName)
            self.logFile.open(QtCore.QIODevice.Append)
            fileInfo = QtCore.QFileInfo(logFileName)
            self.settings.setValue("logging/filename", fileInfo.dir().absolutePath())
            self.logButton.setText("Stop " + fileInfo.fileName())

    def onStatusUpdate(self, message):
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
        c = self.sender()
        # check for name, subscription, etc.
        if Messaging.hdr.GetMessageID(message) == self.connectClass.ID:
            c.name = self.connectClass.GetName(message)
            c.statusLabel.setText(c.name)
        elif Messaging.hdr.GetMessageID(message) == self.subscriptionListClass.ID:
            c.subscriptions = {}
            for idx in range(0,self.subscriptionListClass.GetIDs.count):
                id = self.subscriptionListClass.GetIDs(message, idx)
                if id != 0:
                    c.subscriptions[id] = id
            self.onStatusUpdate("updating subscription for "+c.name+" to " + ', '.join(hex(x) for x in c.subscriptions.keys()))
        elif Messaging.hdr.GetMessageID(message) == self.maskedSubscriptionClass.ID:
            c.subMask = self.maskedSubscriptionClass.GetMask(message)
            c.subValue = self.maskedSubscriptionClass.GetValue(message)
            self.onStatusUpdate("updating subscription for "+c.name+" to id & " + hex(c.subMask) + " == " + hex(c.subValue))
        else:
            #write to log, if log is open
            if self.logFile != None:
                self.logFile.write(message)
        for client in self.clients.values():
            if client != c:
                id = Messaging.hdr.GetMessageID(message)
                if id in client.subscriptions or (id & client.subMask == client.subValue):
                    client.sendMsg(message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    msgServer = MessageServer(sys.argv)
    msgServer.show()

    sys.exit(app.exec_())
