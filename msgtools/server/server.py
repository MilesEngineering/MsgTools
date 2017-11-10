#!/usr/bin/env python3
import sys
import getopt

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging

from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork

from msgtools.server.TcpServer import *
from msgtools.server.WebSocketServer import *

class MessageServer(QtWidgets.QMainWindow):
    def __init__(self, argv):
        QtWidgets.QMainWindow.__init__(self)
        
        self.settings = QtCore.QSettings("MsgTools", "MessageServer")
        self.logFile = None
        self.logFileType = None
        
        self.msgLib = Messaging(None, 0, "NetworkHeader")
        self.networkMsgs = self.msgLib.Messages.Network
        try:
            self.privateSubscriptionListClass = self.networkMsgs.PrivateSubscriptionList
        except AttributeError:
            self.privateSubscriptionListClass = None

        self.clients = {}
        
        self.privateSubscriptions = {}

        self.initializeGui()

        self.tcpServer = TcpServer()
        self.tcpServer.statusUpdate.connect(self.onStatusUpdate)
        self.tcpServer.newConnection.connect(self.onNewConnection)

        self.wsServer = WebSocketServer()
        self.wsServer.statusUpdate.connect(self.onStatusUpdate)
        self.wsServer.newConnection.connect(self.onNewConnection)

        # need a way to make serial= and serial both work!
        try:
            tmpOptions = ['serial=', 'bluetoothSPP=', 'plugin=']
            self.optlist, args = getopt.getopt(sys.argv[1:], '', tmpOptions)
        except getopt.GetoptError:
            pass
        else:
            options = tmpOptions
        try:
            tmpOptions = ['serial', 'bluetoothSPP=', 'plugin=']
            self.optlist, args = getopt.getopt(sys.argv[1:], '', tmpOptions)
        except getopt.GetoptError:
            pass
        else:
            options = tmpOptions

        self.pluginPort = None

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

                name = filename.replace("/", "_")
                self.plugin = importlib.machinery.SourceFileLoader(name, filename).load_module(name)

                self.pluginPort = self.plugin.PluginConnection()
                self.pluginPort.statusUpdate.connect(self.onStatusUpdate)
                self.pluginPort.newConnection.connect(self.onNewConnection)
                self.pluginPort.start()

        self.tcpServer.start()
        self.wsServer.start()
        name = self.tcpServer.serverInfo() + "(TCP) and " + str(self.wsServer.portNumber) + "(WebSocket)"
        self.statusBar().addPermanentWidget(QtWidgets.QLabel(name))
        self.readSettings()

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
        self.statusBar()

    def startLog(self, logFileName):
        if self.logFile:
            self.logFile.close()
            self.logFile = None
        self.logFile = QtCore.QFile(logFileName)
        self.logFile.open(QtCore.QIODevice.Append)
        fileInfo = QtCore.QFileInfo(logFileName)
        self.settings.setValue("logging/filename", fileInfo.dir().absolutePath())
        self.logButton.setText("Stop " + fileInfo.fileName())
    
    def stopLog(self):
        if self.logFile != None:
            self.logFile.close()
            self.logFile = None
            self.logButton.setText("Start Logging")

    def onLogButtonClicked(self):
        if self.logFile != None:
            self.stopLog()
        else:
            currentDateTime = QtCore.QDateTime.currentDateTime()
            defaultFilename = currentDateTime.toString("yyyyMMdd-hhmmss") + ".log"
            logFileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", self.settings.value("logging/filename", ".")+"/"+defaultFilename, "Log Files (*.log)")
            # if they hit cancel, don't do anything
            if not logFileName:
                return
            self.startLog(logFileName)

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

    def onMessageReceived(self, hdr):
        c = self.sender()
        # check for name, subscription, etc.
        if hdr.GetMessageID() == self.networkMsgs.Connect.ID:
            connectMsg = self.networkMsgs.Connect(hdr.rawBuffer())
            c.name = connectMsg.GetName()
            c.statusLabel.setText(c.name)
        elif hdr.GetMessageID() == self.networkMsgs.SubscriptionList.ID:
            c.subscriptions = {}
            subListMsg = self.networkMsgs.SubscriptionList(hdr.rawBuffer())
            for idx in range(0,self.networkMsgs.SubscriptionList.GetIDs.count):
                id = subListMsg.GetIDs(idx)
                if id != 0:
                    c.subscriptions[id] = id
            self.onStatusUpdate("updating subscription for "+c.name+" to " + ', '.join(hex(x) for x in c.subscriptions.keys()))
        elif hdr.GetMessageID() == self.networkMsgs.MaskedSubscription.ID:
            subMsg = self.networkMsgs.MaskedSubscription(hdr.rawBuffer())
            c.subMask = subMsg.GetMask()
            c.subValue = subMsg.GetValue()
            self.onStatusUpdate("updating subscription for "+c.name+" to id & " + hex(c.subMask) + " == " + hex(c.subValue))
        elif hdr.GetMessageID() == self.networkMsgs.StartLog.ID:
            startLog = self.networkMsgs.StartLog(hdr.rawBuffer())
            self.logFileType = startLog.GetLogFileType()
            logFileName = startLog.GetLogFileName()
            if not logFileName:
                logFileName = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss") + ".log"
            self.startLog(logFileName)
        elif hdr.GetMessageID() == self.networkMsgs.StopLog.ID:
            self.stopLog()
        elif self.privateSubscriptionListClass != None and hdr.GetMessageID() == self.privateSubscriptionListClass.ID:
            subListMsg = self.privateSubscriptionListClass(hdr.rawBuffer())
            privateSubs = []
            for idx in range(0,self.privateSubscriptionListClass.GetIDs.count):
                id = subListMsg.GetIDs(idx)
                if id == 0:
                    break
                privateSubs.append(id)
                if id in self.privateSubscriptions:
                    self.privateSubscriptions[id].append(c)
                else:
                    self.privateSubscriptions[id] = [c]
            self.onStatusUpdate("adding Private subscription for "+c.name+": " + ', '.join(hex(x) for x in privateSubs))
        else:
            #write to log, if log is open
            if self.logFile != None:
                if self.logFileType and self.logFileType == "JSON":
                    msgObj = Messaging.MsgFactory(hdr)
                    self.logFile.write(Messaging.toJson(msgObj).encode('utf-8'))
                else:
                    self.logFile.write(hdr.rawBuffer())
            for client in self.clients.values():
                if client != c:
                    id = hdr.GetMessageID()
                    if id in client.subscriptions or (id & client.subMask == client.subValue):
                        try:
                            if id in self.privateSubscriptions:
                                # if it's a "private" message, only give it to clients that specifically said they want it
                                # or to clients that are a hardware link.
                                if client in self.privateSubscriptions[id] or client.isHardwareLink:
                                    client.sendMsg(hdr)
                            else:
                                client.sendMsg(hdr)
                        except Exception as ex:
                            if Messaging.debug:
                                print(ex)
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        if self.pluginPort:
            self.pluginPort.stop()
        super(MessageServer, self).closeEvent(event)

    def readSettings(self):
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))
        self.restoreState(self.settings.value("windowState", QtCore.QByteArray()))

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)

    msgServer = MessageServer(sys.argv)
    msgServer.show()

    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
