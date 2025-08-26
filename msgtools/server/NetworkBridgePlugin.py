#!/usr/bin/en"v python3
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject

from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderTranslator, HeaderHelper
from msgtools.lib.client_connection import ClientConnection

import sys

class NetworkBridgeConnection(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)

    def __init__(self, header_class, name, bridge_name):
        super(NetworkBridgeConnection, self).__init__(None)
        
        self.settings = QtCore.QSettings("MsgTools", "MessageServer/%s" % (name))
        
        self.remove_client_btn = QtWidgets.QPushButton("Remove")
        self.remove_client_btn.pressed.connect(self._on_removed)

        # button to open/close bridge port
        self.open_close_button = QtWidgets.QPushButton("Open")
        self.open_close_button.pressed.connect(self._open_close_switch)

        # button select new network bridge port
        self.choose_bridge_button = QtWidgets.QPushButton("Select Bridge Server")
        self.choose_bridge_button.pressed.connect(self._choose_bridge)

        self.status_label = QtWidgets.QLabel()
        self.rxMsgCount = 0
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = True
        
        # if port not specified, default to last used port
        if bridge_name:
            self.bridge_name = bridge_name
        else:
            self.bridge_name = self.settings.value("bridge_name", None)

        self.network_bridge = ClientConnection(header_class)
        self.network_bridge.connection_error.connect(self._display_connect_error)
        self.network_bridge.rx_hdr.connect(self.network_bridge_rx)
        self.network_bridge.on_connect.connect(self._on_connected)
        self.network_bridge.on_disconnect.connect(self._on_disconnect)
        self.name = name
        self.status_label.setText(self.name)
        
        self.reopenTimer = QtCore.QTimer(self)
        self.reopenTimer.setInterval(1000)
        self.reopenTimer.timeout.connect(self._open_network_bridge)

        self.header_class = header_class
        if header_class == Messaging.hdr:
            self.header_translator = None
        else:
            self.header_translator = HeaderTranslator(header_class, Messaging.hdr)

        self.tmpRxHdr = None

    def widget(self, index):
        if index == 0:
            return self.remove_client_btn
        if index == 1:
            return self.open_close_button
        if index == 2:
            return self.choose_bridge_button
        if index == 3:
            return self.status_label
        return None
    
    def _open_network_bridge(self):
        if self.network_bridge.isOpen() or not self.bridge_name:
            # if we're already open, or we haven't been configured,
            # make sure we stop retrying to open
            self.reopenTimer.stop()
        else:
            self.network_bridge.OpenConnection(self.bridge_name)
            self.statusUpdate.emit("Opened %s on port %s" % (self.name, self.bridge_name))
            self.open_close_button.setText("Close")
            self.settings.setValue("bridge_name", self.bridge_name)
            self.reopenTimer.stop()

    def _close_network_bridge(self):
        self.network_bridge.CloseConnection()
        self.open_close_button.setText("Open")

    def _open_close_switch(self):
        # open or close the port
        if self.network_bridge.isOpen():
            self._close_network_bridge()
            self.statusUpdate.emit("Closed %s on port %s" % (self.name, self.bridge_name))
        else:
            self._open_network_bridge()

    def _choose_bridge(self):
        user_input, ok = QtWidgets.QInputDialog.getText(None, 'Connect',  'Server:', QtWidgets.QLineEdit.Normal, self.bridge_name)
        if ok:
            self._close_network_bridge()
            self.bridge_name = user_input
            self._open_network_bridge()

    def start(self):
        self._open_close_switch()

    def print_error(self, errType):
        print(errType)
        sys.stdout.flush()

    def stop(self):
        pass

    def network_bridge_rx(self, bridge_hdr):
        if self.header_translator:
            network_hdr = self.header_translator.translate(bridge_hdr)
            # if we can't translate the message, just return
            if network_hdr == None:
                return
        else:
            network_hdr = bridge_hdr
        self.messagereceived.emit(network_hdr)

    def sendMsg(self, network_hdr):
        if self.header_translator:
            bridge_hdr = self.header_translator.translate(network_hdr)
            # if we can't translate the message, just return
            if bridge_hdr == None:
                return
        else:
            bridge_hdr = network_hdr

        self.network_bridge.SendHeader(bridge_hdr)

    def _on_removed(self):
        self.disconnected.emit(self)

    def _on_connected(self):
        self.open_close_button.setText("Close")
        # send a connect message
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName(self.name)
        self.sendMsg(connectMsg.hdr)
        # send a subscription message
        subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
        self.sendMsg(subscribeMsg.hdr)

    def _on_disconnect(self):
        self.open_close_button.setText("Open")

    def _display_connect_error(self, socketError):
        self.statusUpdate.emit('Not Connected('+str(socketError)+'), '+self.network_bridge.connection.errorString())

def NetworkBridgePluginConnection(param=None):
    from NetworkHeader import NetworkHeader
    return NetworkBridgeConnection(NetworkHeader, "NetworkBridge", param)

def NetworkBridgePluginEnabled():
    return True

def CosmosPluginConnection(param=None):
    try:
        from CosmosHeader import CosmosHeader
        return NetworkBridgeConnection(CosmosHeader, "CosmosBridge", param)
    except:
        return None

def CosmosPluginEnabled():
    try:
        from CosmosHeader import CosmosHeader
        return True
    except:
        return False

import collections
PluginInfo = collections.namedtuple('PluginInfo', ['name', 'enabled', 'connect_function'])
network_bridge_plugin_info = PluginInfo('NetworkBridge', NetworkBridgePluginEnabled, NetworkBridgePluginConnection)
cosmos_plugin_info = PluginInfo('Cosmos', CosmosPluginEnabled, CosmosPluginConnection)
