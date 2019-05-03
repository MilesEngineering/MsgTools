from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject

from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderTranslator
from BluetoothHeader import BluetoothHeader

BTHS = BluetoothHeader.SIZE

# We require bluez, available on Windows and Linux
import bluetooth
import threading
import select
import time

class BluetoothRFCOMMConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)

    def __init__(self, deviceBTAddr, deviceBTPort=None):
        super(BluetoothRFCOMMConnection, self).__init__(None)

        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(self.onDisconnected)

        self.statusLabel = QtWidgets.QLabel()
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = True
        self.basetime = time.time()
        
        if deviceBTPort is None:
            services = bluetooth.find_service(address=deviceBTAddr,
                                              uuid='00001101-0000-1000-8000-00805F9B34FB')
            if len(services)<=0:
                deviceBTPort = 8
            else:
                deviceBTPort = services[0]['port']
        
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((deviceBTAddr, deviceBTPort))
        #self.socket.disconnected.connect(self.onDisconnected)

        self.btsock_buffer = b''
        self.btsock_outgoing = b''

        self.hdrTranslator = HeaderTranslator(BluetoothHeader, Messaging.hdr)
        
        self.name = "Bluetooth RFCOMM " + deviceBTAddr
        self.statusLabel.setText(self.name)

        self.thread = threading.Thread(target=self.rfcommThread)
        self.thread.daemon = True
        self.thread.start()

    def start(self):
        pass

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.statusLabel
        return None

    def rfcommThread(self):
        while True:
            ret = select.select([self.socket],
                                [self.socket],
                                [],
                                0.1)
            if len(ret[2]) > 0:
                #self.statusUpdate.emit("some message?")
                self.socket.close()
                return

            if len(ret[0]) > 0:
                # we've got data to read
                self.btsock_buffer += self.socket.recv(4096)

            if len(self.btsock_outgoing)>0 and len(ret[1])>0:
                sent = self.socket.send(self.btsock_outgoing)
                self.btsock_outgoing = self.btsock_outgoing[sent:]

            while len(self.btsock_buffer) >= BTHS:
                hdr = BluetoothHeader(self.btsock_buffer[0:BTHS])
                total_len = BTHS + hdr.GetDataLength()
                if len(self.btsock_buffer) >= total_len:
                    # we've got enough data for the whole message
                    hdr = BluetoothHeader(self.btsock_buffer)
                    self.btsock_buffer = self.btsock_buffer[total_len:]
                    
                    networkMsg = self.hdrTranslator.translate(hdr)
                    
                    self.messagereceived.emit(networkMsg)
                else:
                    # we don't quite have enough data for a whole message
                    break

    def onDisconnected(self):
        print("self.disconnected.emit(self)")
        self.socket.close()
        self.disconnected.emit(self)
        print("self.disconnected.emit(self)")

    def sendMsg(self, networkMsg):
        btMsg = self.hdrTranslator.translate(networkMsg)
        # if we can't translate the message, just return
        if btMsg == None:
            return
        self.btsock_outgoing += btMsg.rawBuffer().raw

    def stop(self):
        pass

def PluginConnection(param=""):
    btArgs = param.split(",")
    if len(btArgs)>1:
        btArgs[1] = int(btArgs[1])
    return BluetoothRFCOMMConnection(*btArgs)

def PluginEnabled():
    return True

import collections
PluginInfo = collections.namedtuple('PluginInfo', ['name', 'enabled', 'connect_function'])
plugin_info = PluginInfo('Bluetooth RF Comm', PluginEnabled, PluginConnection)
