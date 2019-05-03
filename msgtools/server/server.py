#!/usr/bin/env python3
import os
import sys
import argparse
import traceback
import pkg_resources

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
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

class SelectPluginDialog(QtWidgets.QDialog):
    pluginSelected = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        super(SelectPluginDialog, self).__init__(parent)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle("Select a PLugin")
        
        self.resize(600, 200)

        self.pluginList = QtWidgets.QTreeWidget()
        openButton = QtWidgets.QPushButton("Load")
        openButton.clicked.connect(self.loadPlugin)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.pluginList)
        layout.addWidget(openButton)
        self.setLayout(layout)

        tableHeader = ["Name", "Module"]
        self.pluginList.setHeaderLabels(tableHeader)
        for entry_point in pkg_resources.iter_entry_points("msgtools.server.plugin"):
            try:
                plugin_entry_point = entry_point.load()
                try:
                    pluginInfo = plugin_entry_point
                    if pluginInfo.enabled():
                        list = [pluginInfo.name, entry_point.module_name]
                        item = QtWidgets.QTreeWidgetItem(None, list)
                        item.plug_entrypoint_name = entry_point.name
                        self.pluginList.addTopLevelItem(item)
                    else:
                        if Messaging.debug:
                            print("Ignoring plugin %s %s:%s is disabled" % (entry_point.name, entry_point.module_name, entry_point.attrs[0]))
                except AttributeError as e:
                    if Messaging.debug:
                        print("    " + str(e))
                        print("No info in %s %s:%s!  must be function" % (entry_point.name, entry_point.module_name, entry_point.attrs[0]))
                    list = [entry_point.name, entry_point.module_name]
                    item = QtWidgets.QTreeWidgetItem(None, list)
                    item.plug_entrypoint_name = entry_point.name
                    self.pluginList.addTopLevelItem(item)
            except Exception as e:
                if Messaging.debug:
                    print(e)
                    import traceback
                    print(traceback.format_exc())                    
                    print("Ignoring plugin %s %s:%s, exception while loading" % (entry_point.name, entry_point.module_name, entry_point.attrs[0]))
        for i in range(0, len(tableHeader)):
            self.pluginList.resizeColumnToContents(i)
        
    def loadPlugin(self):
        cur_item = self.pluginList.currentItem()
        if cur_item is not None:
            self.pluginSelected.emit(cur_item.plug_entrypoint_name)
            self.close()

class MessageServer(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        
        self.settings = QtCore.QSettings("MsgTools", "MessageServer")
        self.logFile = None
        self.logFileType = None
        
        parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG, 
            formatter_class=argparse.RawDescriptionHelpFormatter)

        # iterate over plugins, and setup argparse for each
        for entry_point in pkg_resources.iter_entry_points("msgtools.server.plugin"):
            parser.add_argument(
                '--%s' %entry_point.name,
                dest='last%s'%entry_point.name,
                action='store_true',
                help='''Load the %s plugin via %s:%s''' % (entry_point.name, entry_point.module_name, entry_point.attrs[0]))
            parser.add_argument(
                '--%s='%entry_point.name,
                dest= entry_point.name,
                help="Same as above, passing param %s to the plugin" % (entry_point.name.upper()))

        parser.add_argument('--plugin', help='Specify a filesystem path to a plugin module to load.')
        parser.add_argument('--msgdir', 
            help='''Specify the directory for generated python code to use for headers, and other 
                    message definitions''')
        parser.add_argument('--port', type=int, 
            help='The TCP port to use.  Websockets are always TCP port + 1.')
        parser.add_argument('--debug', action='store_true', help='Set if you want extra error info printed to stdout.')

        # if we had plugins before, but no cmdline args now, add simulated
        # cmdline args for our old plugins
        if len(sys.argv) == 1:
            last_plugins = self.settings.value("pluginsLoaded", "", str).split("|")
            for plugin in last_plugins:
                if plugin:
                    sys.argv.append("--"+plugin)

        args = parser.parse_args()
        
        Messaging.debug = False if hasattr(args, 'debug') == False else args.debug
        
        try:
            Messaging.LoadAllMessages(searchdir=args.msgdir)
        except ImportError:
            print("\nERROR! Auto-generated python code not found!")
            print("cd to a directory downstream from a parent of obj/CodeGenerator/Python")
            print("or specify that directory with --msgdir=PATH\n")
            quit()

        self.networkMsgs = Messaging.Messages.Network

        self.clients = {}
        
        self.privateSubscriptions = {}

        self.initializeGui()

        self.pluginPorts = []
        tcpport = 5678
        wsport = 5679

        if args.port is not None:
            tcpport = args.port
            wsport = tcpport+1
        
        for entry_point in pkg_resources.iter_entry_points("msgtools.server.plugin"):
            # check for argparse data for the plugin
            plugin_option = getattr(args, entry_point.name)
            plugin_last_option = getattr(args, 'last'+entry_point.name)
            if plugin_last_option is not False or plugin_option is not None:
                param = plugin_option if plugin_option is not None else None
                self.load_plugin(entry_point.name, entry_point, param)

        # load plugin via path to .py file
        if args.plugin is not None:
            filename = args.plugin
            import os
            moduleName = os.path.splitext(os.path.basename(filename))[0]
            if Messaging.debug:
                print("loading module %s as %s" % (filename, moduleName))

            name = filename.replace("/", "_")
            import importlib
            self.plugin = importlib.machinery.SourceFileLoader(name, filename).load_module(name)

            pluginPort = self.plugin.PluginConnection(None)
            pluginPort.statusUpdate.connect(self.onStatusUpdate)
            # try to allow plugin to emit new connections
            try:
                pluginPort.newConnection.connect(self.onNewConnection)
            except AttributeError:
                # if that fails, just use the plugin as one new connection.
                self.onNewConnection(pluginPort)
            pluginPort.start()
            self.pluginPorts.append(pluginPort)

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

        # Components

        # if started via invoking this file directly (like would happen with source sitting on disk),
        # do not show the button to load plugins, since that only works with installed plugins.
        if __name__ != "__main__":
            self.addPluginButton = QtWidgets.QPushButton("Load Plugin")
            self.addPluginButton.pressed.connect(self.onAddPluginClicked)
            vbox.addWidget(self.addPluginButton)

        self.logButton = QtWidgets.QPushButton("Start Logging")
        self.logButton.pressed.connect(self.onLogButtonClicked)
        vbox.addWidget(self.logButton)

        self.grid = QtWidgets.QGridLayout()
        vbox.addLayout(self.grid)
        
        self.statusBox = QtWidgets.QPlainTextEdit()
        vbox.addWidget(self.statusBox)

        # Central Widget (QMainWindow limitation)
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(vbox)
        self.setCentralWidget(centralWidget)

        # Main Window Stuff
        self.setWindowTitle("MessageServer 0.1")
        self.statusBar()

    def startLog(self, log_name):
        if self.logFile:
            self.logFile.close()
            self.logFile = None
        if log_name.endswith("json"):
            self.logFileType = "json"
        elif log_name.endswith("csv"):
            self.logFileType = "csv"
            # hash table of booleans for if each type of message has had it's header
            # put into this log file already.
            self.loggedMsgHeaderRow = {}
        elif log_name.endswith('bin') or log_name.endswith('log'):
            self.logFileType = "bin"
        else:
            print("ERROR!  Invalid log type " + log_name)
        self.logFile = QtCore.QFile(log_name)
        self.logFile.open(QtCore.QIODevice.Append)
        fileInfo = QtCore.QFileInfo(log_name)
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
                if self.logFileType == "json":
                    logStatusMsg.SetLogFileType("JSON")
                elif self.logFileType == "csv":
                    logStatusMsg.SetLogFileType("CSV")
                elif self.logFileType == "bin":
                    logStatusMsg.SetLogFileType("BIN")
            for client in self.clients.values():
                client.sendMsg(logStatusMsg.hdr)

    def onLogButtonClicked(self):
        if self.logFile != None:
            self.stopLog()
        else:
            currentDateTime = QtCore.QDateTime.currentDateTime()
            defaultFilename = currentDateTime.toString("yyyyMMdd-hhmmss") + ".log"
            logFileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", self.settings.value("logging/filename", ".")+"/"+defaultFilename, "Log Files (*.log);;JSON Files (*.json);;CSV Files (*.csv)")
            # if they hit cancel, don't do anything
            if not logFileName:
                return
            self.startLog(logFileName)
    
    def onAddPluginClicked(self):
        d = SelectPluginDialog()
        d.pluginSelected.connect(self.pluginSelected)
        d.exec_()
    
    def pluginSelected(self, plugin_name):
        for entry_point in pkg_resources.iter_entry_points("msgtools.server.plugin"):
            if entry_point.name == plugin_name:
                self.load_plugin(plugin_name, entry_point, None)
                return

    def load_plugin(self, plugin_name, entry_point, param):
        try:
            # load the module, create the plugin
            plugin_entry_point = entry_point.load()
            try:
                # check for the entry point giving a struct with a 'connection' attribute
                pluginCreatorFn = plugin_entry_point.connect_function
            except AttributeError:
                pluginCreatorFn = plugin_entry_point
            pluginPort = pluginCreatorFn()
            pluginPort.plugin_name = plugin_name
        except:
            a,b,c = sys.exc_info()
            exc = ''.join(traceback.format_exception(a,b,c))
            self.onStatusUpdate("Exception loading plugin:\n%s" % (exc))
            print(exc)
            return
        
        # connect plugin to our status update function
        pluginPort.statusUpdate.connect(self.onStatusUpdate)
        
        # try to allow plugin to emit new connections
        try:
            pluginPort.newConnection.connect(self.onNewConnection)
        except AttributeError:
            # if that fails, just use the plugin as one new connection.
            self.onNewConnection(pluginPort)
        
        pluginPort.start()
        self.pluginPorts.append(pluginPort)

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
        # remove the plugin, if it is one
        try:
            self.pluginPorts.remove(connection)
        except ValueError:
            pass
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

    def logMsg(self, hdr):
        #write to log, if log is open
        if self.logFile != None:
            log = ''
            if self.logFileType == "csv":
                msg = Messaging.MsgFactory(hdr)
                if not msg.MsgName() in self.loggedMsgHeaderRow:
                    self.loggedMsgHeaderRow[msg.MsgName()] = True
                    log = msg.csvHeader(timeColumn=True)+'\n'
                log += msg.toCsv(timeColumn=True)+'\n'
                log = log.encode('utf-8')
            elif self.logFileType == "json":
                msg = Messaging.MsgFactory(hdr)
                log = msg.toJson(includeHeader=True)+'\n'
                log = log.encode('utf-8')
            elif self.logFileType == "bin":
                log = hdr.rawBuffer().raw
            self.logFile.write(log)
            self.logFile.flush()

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
            self.logMsg(hdr)

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
            self.logMsg(hdr)

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
                            a,b,c = sys.exc_info()
                            exc = ''.join(traceback.format_exception(a,b,c))
                            self.onStatusUpdate("Exception in server.py while sending to client %s:\n%s" % (client.name, exc))
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        pluginNames = []
        for pluginPort in self.pluginPorts:
            try:
                pluginNames.append(pluginPort.plugin_name)
            except AttributeError:
                pass
            pluginPort.stop()
        self.settings.setValue("pluginsLoaded", "|".join(pluginNames))
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
