#!/usr/bin/env python3
import sys
import argparse

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

DESCRIPTION='''
    MsgServer acts as a central routing hub for one or more message clients.
    Messages received, are reflected onto all other client connections.
    Bluetooth (RFCOMM), TCP, Websocket, and USB Serial clients are all
    supported.  

    MsgServer also provides binary logging capability from from both the UI
    and Network.xLogx messages.  Message masks and subscription are also
    supported through subscription messages defined in the Network 
    group.
'''

EPILOG='''

Headers
=======
MsgServer expects headers.NetworkHeader as the prequel for all messages.  
All clients need to send and receive messages with a NetworkHeader.

TCP and Websockets
==================
MsgServer always runs a TCP and Websocket server.  The Websocket server
port is always one greater than the TCP port.  The default ports are
5678 and 5679 for TCP and Websockets respectively.

SPP and RFCOMM
==============
SPP ("Serial Port Profile") is a Bluetooth service profile for emulating 
an RS232 serial connection over Bluetooth. To accomplish this, SPP uses an 
RFCOMM (a reliable stream-oriented connection; the TCP of the Bluetooth 
world) socket to move the data.  SPP provides RS-232 signaling concepts
for CTS, RTS, etc.

BluetoothRFCOMMQt
=================
* Requires Qt
* Works on Mac and Linux.

BluetoothRFCOMM
===============
* Requires PyBlueZ which may not be available for Python versions after 3.5
* Works on Windows and Linux

Bluetooth Arguments
===================
Both command line options take a Bluetooth MAC address, and optionally 
an RFCOMM port to connect to. For instance: 

    --bluetoothRFCOMM=00:de:ad:be:ef:77,8

If you omit the port (",8", above), then the code will attempt to use 
Bluetooth SDP to find an SPP service on the target device; if multiple 
services are available, an arbitrary one will be chosen.

Bluetooth Troubleshooting
=========================
If you can't connect to your device, try pairing it with your PC first.
Sometimes devices require pairing before allowing an arbitrary connection.

Examples
========
    msgserver &

    Will run MsgServer on the default TCP Websocket ports 5678 and 5679.

    msgserver --serial

    Will run MsgServer with a serial port input on the last used port, 
    and TCP/Websocket on 5678, and 5679 respectively.

    msgserver --serial= /dev/tty12

    Will run MsgServer with a serial port connected on /dev/tty12. and
    a TCP/Websocket port on 5678, and 5679 respectively.

    msgserver --port 1234

    Will run MsgServer with a TCP port on 1234 and Websocket port on 1235

    msgserver --bluetoothRFCOMM=00:de:ad:be:ef:77

    Will run MsgServer on the default TCP/Websocket ports and attempt to connect
    to the indicated Bluetooth MAC.  SDP will be used to try and discover
    the appropriate channel.


    msgserver --bluetoothRFCOMM=00:de:ad:be:ef:77,8

    Will run MsgServer on the default TCP/Websocket ports and attempt to connect
    to the indicated Bluetooth MAC and channel 8.

'''

class MessageServer(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        self.settings = QtCore.QSettings("MsgTools", "MessageServer")
        self.logFile = None
        self.logFileType = None

        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG, 
            formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('--serial', dest='lastserial', action='store_true', 
            help='Use a serial port input on the last used port' )
        parser.add_argument('--serial=', dest='serial', 
            help='''Use a serial port input with the specified serial port name.  This
                    form takes precedence over --serial if both are specified.''' )
        parser.add_argument('--bluetoothSPP', 
            help='Use a Bluetooth SPP connection to the indicated port.  See below for details.')
        parser.add_argument('--bluetoothRFCOMM', 
            help='Use a Bluetooth RFCOMM connection to the indicated port.  See below for details.')
        parser.add_argument('--bluetoothRFCOMMQt', 
            help='Use a QT Bluetooth RFCOMM connection on the indicated port. See below for details.')
        parser.add_argument('--plugin', help='Specify a plugin module to use')
        parser.add_argument('--msgdir', 
            help='''Specify the directory for generated python code to use for headers, and other 
                    message definitions''')
        parser.add_argument('--port', type=int, 
            help='The TCP port to use.  Websockets are always TCP port + 1.')

        args = parser.parse_args()
        
        try:
            self.msgLib = Messaging(args.msgdir, False, "NetworkHeader")
        except ImportError:
            print("\nERROR! Auto-generated python code not found!")
            print("cd to a directory downstream from a parent of obj/CodeGenerator/Python")
            print("or specify that directory with --msgdir=PATH\n")
            quit()

        self.networkMsgs = self.msgLib.Messages.Network

        self.clients = {}
        
        self.privateSubscriptions = {}

        self.initializeGui()

        self.pluginPort = None
        tcpport = 5678
        wsport = 5679

        if args.port is not None:
            tcpport = args.port
            wsport = tcpport+1
        
        if args.lastserial is not False or args.serial is not None:
            from SerialHeader import SerialHeader
            from msgtools.server.SerialPlugin import SerialConnection
            serialPortName = args.serial if args.serial is not None else None
            self.serialPort = SerialConnection(SerialHeader, serialPortName)
            self.serialPort.statusUpdate.connect(self.onStatusUpdate)
            self.onNewConnection(self.serialPort)
            self.serialPort.start()
        
        if args.bluetoothSPP is not None:
            from BluetoothHeader import BluetoothHeader
            from msgtools.server.SerialPlugin import SerialConnection
            bluetoothPortName = args.bluetoothSPP
            self.bluetoothPort = SerialConnection(BluetoothHeader, bluetoothPortName)
            self.bluetoothPort.statusUpdate.connect(self.onStatusUpdate)
            self.onNewConnection(self.bluetoothPort)
            self.bluetoothPort.start()

        if args.bluetoothRFCOMM is not None:
            from msgtools.server.BluetoothRFCOMM import BluetoothRFCOMMConnection
            btArgs = args.bluetoothRFCOMM.split(",")
            if len(btArgs)>1:
                btArgs[1] = int(btArgs[1])
            self.bluetoothPort = BluetoothRFCOMMConnection(*btArgs)
            self.bluetoothPort.statusUpdate.connect(self.onStatusUpdate)
            self.onNewConnection(self.bluetoothPort)
        
        if args.bluetoothRFCOMMQt is not None:
            from msgtools.server.BluetoothRFCOMMQt import BluetoothRFCOMMQtConnection
            from PyQt5 import QtBluetooth
            btArgs = args.bluetoothRFCOMMQt.split(",")
            btHost = btArgs[0]
            if len(btArgs)>1:
                btPort = int(btArgs[1])
            else:
                btPort = 8
            self.btSocket = QtBluetooth.QBluetoothSocket(QtBluetooth.QBluetoothServiceInfo.RfcommProtocol)
            self.btSocket.connectToService(QtBluetooth.QBluetoothAddress(btHost), btPort)
            self.bluetoothPort = BluetoothRFCOMMQtConnection(self.btSocket)
            self.bluetoothPort.statusUpdate.connect(self.onStatusUpdate)
            self.onNewConnection(self.bluetoothPort)
        
        if args.plugin is not None:
            filename = args.plugin
            import os
            moduleName = os.path.splitext(os.path.basename(filename))[0]
            if Messaging.debug:
                print("loading module ", filename, "as",moduleName)

            name = filename.replace("/", "_")
            import importlib
            self.plugin = importlib.machinery.SourceFileLoader(name, filename).load_module(name)

            self.pluginPort = self.plugin.PluginConnection()
            self.pluginPort.statusUpdate.connect(self.onStatusUpdate)
            self.pluginPort.newConnection.connect(self.onNewConnection)
            self.pluginPort.start()

        self.tcpServer = TcpServer(tcpport)
        self.tcpServer.statusUpdate.connect(self.onStatusUpdate)
        self.tcpServer.newConnection.connect(self.onNewConnection)

        self.wsServer = WebSocketServer(wsport)
        self.wsServer.statusUpdate.connect(self.onStatusUpdate)
        self.wsServer.newConnection.connect(self.onNewConnection)

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
        self.queryLog()
    
    def stopLog(self):
        if self.logFile != None:
            self.logFile.close()
            self.logFile = None
            self.logButton.setText("Start Logging")
            self.queryLog()

    def queryLog(self):
        if hasattr(self.networkMsgs, 'LogStatus'):
            logStatusMsg = self.networkMsgs.LogStatus()
            if self.logFile != None:
                logStatusMsg.SetLogOpen(1)
                logStatusMsg.SetLogFileName(self.logFile.fileName())
                if self.logFileType == "JSON":
                    logStatusMsg.SetLogFileType("JSON")
            for client in self.clients.values():
                client.sendMsg(logStatusMsg.hdr)

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

    def logMessage(self, hdr):
        #write to log, if log is open
        if self.logFile != None:
            if self.logFileType and self.logFileType == "JSON":
                msgObj = Messaging.MsgFactory(hdr)
                self.logFile.write(Messaging.toJson(msgObj).encode('utf-8'))
            else:
                self.logFile.write(hdr.rawBuffer().raw)

    def onMessageReceived(self, hdr):
        c = self.sender()
        # check for name, subscription, etc.
        if hasattr(self.networkMsgs, 'Connect') and hdr.GetMessageID() == self.networkMsgs.Connect.ID:
            connectMsg = self.networkMsgs.Connect(hdr.rawBuffer())
            c.name = connectMsg.GetName()
            c.statusLabel.setText(c.name)
        elif hasattr(self.networkMsgs, 'SubscriptionList') and hdr.GetMessageID() == self.networkMsgs.SubscriptionList.ID:
            c.subscriptions = {}
            subListMsg = self.networkMsgs.SubscriptionList(hdr.rawBuffer())
            for idx in range(0,self.networkMsgs.SubscriptionList.GetIDs.count):
                id = subListMsg.GetIDs(idx)
                if id != 0:
                    c.subscriptions[id] = id
            self.onStatusUpdate("updating subscription for "+c.name+" to " + ', '.join(hex(x) for x in c.subscriptions.keys()))
        elif hasattr(self.networkMsgs, 'MaskedSubscription') and hdr.GetMessageID() == self.networkMsgs.MaskedSubscription.ID:
            subMsg = self.networkMsgs.MaskedSubscription(hdr.rawBuffer())
            c.subMask = subMsg.GetMask()
            c.subValue = subMsg.GetValue()
            self.onStatusUpdate("updating subscription for "+c.name+" to id & " + hex(c.subMask) + " == " + hex(c.subValue))
        elif hasattr(self.networkMsgs, 'StartLog') and hdr.GetMessageID() == self.networkMsgs.StartLog.ID:
            startLog = self.networkMsgs.StartLog(hdr.rawBuffer())
            self.logFileType = startLog.GetLogFileType()
            logFileName = startLog.GetLogFileName()
            if not logFileName:
                logFileName = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd-hhmmss") + ".log"
            self.startLog(logFileName)
        elif hasattr(self.networkMsgs, 'StopLog') and hdr.GetMessageID() == self.networkMsgs.StopLog.ID:
            self.stopLog()
        elif hasattr(self.networkMsgs, 'QueryLog') and hdr.GetMessageID() == self.networkMsgs.QueryLog.ID:
            self.queryLog()
        elif hasattr(self.networkMsgs, 'ClearLogs') and hdr.GetMessageID() == self.networkMsgs.ClearLogs.ID:
            # This message was added more for AndroidServer. Plenty of other good ways to delete a log on 
            # a desktop or other more capable machine. That said, silently eat the request - blindly forwarding
            # this along could be hazardous.
            pass
        elif hasattr(self.networkMsgs, 'Note') and hdr.GetMessageID() == self.networkMsgs.Note.ID:
            # The Note message allows a user to annotate a log.  We want to drop it into the log, but not
            # forward to all other clients.
            self.logMessage(hdr)

        elif hasattr(self.networkMsgs, 'PrivateSubscriptionList') and  hdr.GetMessageID() == self.networkMsgs.PrivateSubscriptionList.ID:
            subListMsg = self.networkMsgs.PrivateSubscriptionList(hdr.rawBuffer())
            privateSubs = []
            for idx in range(0,self.networkMsgs.PrivateSubscriptionList.GetIDs.count):
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
            # Log the message
            self.logMessage(hdr)

            # Route to all clients
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
                            self.onStatusUpdate("Exception in server.py while sending to client " + client.name + ": ["  +str(ex)+"]")
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

    msgServer = MessageServer()
    msgServer.show()

    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
