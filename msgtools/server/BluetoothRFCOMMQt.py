from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork
from PyQt5.QtCore import QObject

from msgtools.lib.messaging import Messaging
from BluetoothHeader import BluetoothHeader
from NetworkHeader import NetworkHeader

# We require Qt Bluetooth support, available on Linux and Macs(?)

class BluetoothRFCOMMQtConnection(QObject):
    disconnected = QtCore.pyqtSignal(object)
    messagereceived = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)

    def __init__(self, socket):
        super(BluetoothRFCOMMQtConnection, self).__init__(None)

        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(lambda: self.socket.close())
        self.statusLabel = QtWidgets.QLabel()
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = True

        self.socket = socket
        self.socket.readyRead.connect(self.onReadyRead)
        self.socket.disconnected.connect(self.onDisconnected)

        self.hdrTranslator = Messaging.HeaderTranslator(BluetoothHeader, NetworkHeader)
        
        self.rxBuffer = bytearray()

        self.name = "Bluetooth RFCOMM " + self.socket.peerAddress().toString()
        self.statusLabel.setText(self.name)

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.statusLabel
        return None
            
    def onReadyRead(self):
        inputStream = QtCore.QDataStream(self.socket)

        while(1):
            if len(self.rxBuffer) < BluetoothHeader.SIZE:
                if self.socket.bytesAvailable() < BluetoothHeader.SIZE:
                    return
                self.rxBuffer += inputStream.readRawData(BluetoothHeader.SIZE - len(self.rxBuffer))

            if len(self.rxBuffer) >= BluetoothHeader.SIZE:
                hdr = BluetoothHeader(self.rxBuffer)
                bodyLen = hdr.GetDataLength()
                if len(self.rxBuffer)+self.socket.bytesAvailable() < BluetoothHeader.SIZE + bodyLen:
                    return

                self.rxBuffer += inputStream.readRawData(BluetoothHeader.SIZE + bodyLen - len(self.rxBuffer))

                # create a new header object with the appended body
                btHdr = BluetoothHeader(self.rxBuffer)

                # if we got this far, we have a whole message! So, emit the signal
                networkMsg = self.hdrTranslator.translate(btHdr)

                self.messagereceived.emit(networkMsg)

                # then clear the buffer, so we start over on the next message
                self.rxBuffer = bytearray()

    def onDisconnected(self):
        self.disconnected.emit(self)

    def sendMsg(self, networkMsg):
        btMsg = self.hdrTranslator.translate(networkMsg)
        # if we can't translate the message, just return
        if btMsg == None:
            return
        self.socket.write(btMsg.rawBuffer().raw)
