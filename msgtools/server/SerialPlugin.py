#!/usr/bin/en"v python3
from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import QObject
from PyQt5.QtSerialPort import QSerialPort

from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderTranslator
from msgtools.server import SerialportDialog

import struct
import sys

def Crc16(data):
    crc = 0;
    for i in range(0,len(data)):
        d = struct.unpack_from('B', data, i)[0]
        crc = (crc >> 8) | (crc << 8)
        crc ^= d
        crc ^= (crc & 0xff) >> 4
        crc ^= crc << 12
        crc = 0xFFFF & crc
        crc ^= (crc & 0xff) << 5
        crc = 0xFFFF & crc
    return crc

def hexbytes(hdr):
    try:
        b = hdr.rawBuffer()[:]
    except:
        b = hdr
    return "0x"+":".join("{:02x}".format(c) for c in b)

class BaseSerialConnection(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)
    def __init__(self, name, portName, baud_rate=QSerialPort.Baud115200, parity=QSerialPort.NoParity):
        super(BaseSerialConnection, self).__init__(None)
        
        self.base_name = name
        self.settings = QtCore.QSettings("MsgTools", "MessageServer/"+self.base_name)
        
        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(self.onDisconnected)

        # button to open/close serial port
        self.openCloseButton = QtWidgets.QPushButton("button")
        self.openCloseButton.pressed.connect(self.openCloseSwitch)
        
        # button select new serial port
        self.selectPortButton = QtWidgets.QPushButton("Select Port")
        self.selectPortButton.pressed.connect(self.selectPort)

        self.statusLabel = QtWidgets.QLabel()
        self.rxMsgCount = 0
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = True
        
        # if port not specified, default to last used port
        if not portName:
            portName = self.settings.value("portName", None)

        self.serialPort = QSerialPort(portName)
        self.serialPort.setBaudRate(baud_rate)
        self.serialPort.setFlowControl(QSerialPort.NoFlowControl)
        self.serialPort.setParity(parity)
        self.serialPort.setDataBits(QSerialPort.Data8)
        self.serialPort.setStopBits(QSerialPort.OneStop)
        self.serialPort.errorOccurred.connect(self.onSerialError)

        self.serialPort.readyRead.connect(self.onReadyRead)
        self.name = self.base_name + " " + self.serialPort.portName()
        self.statusLabel.setText(self.name)
        
        self.reopenTimer = QtCore.QTimer(self)
        self.reopenTimer.setInterval(1000)
        self.reopenTimer.timeout.connect(self._openSerialPort)

    def onDisconnected(self):
        self.disconnected.emit(self)
    
    def onSerialError(self, error):
        if error == QSerialPort.NoError:
            pass
        elif error == QSerialPort.ReadError:
            self.statusUpdate.emit("Error, Closing SerialPort on port "+str(self.serialPort.portName()))
            self._closeSerialPort()
            # Don't restart the timer if it's active.
            # If we did, then a steady stream of errors would keep resetting
            # the timer, and it would never go off.
            if not self.reopenTimer.isActive():
                self.reopenTimer.start()
        elif error == QSerialPort.ResourceError:
            pass

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.openCloseButton
        if index == 2:
            return self.selectPortButton
        if index == 3:
            return self.statusLabel
        return None
    
    def _openSerialPort(self):
        if self.serialPort.isOpen():
            # if we're already open, make sure we stop retrying to open
            self.reopenTimer.stop()
        else:
            if self.serialPort.open(QSerialPort.ReadWrite):
                self.statusUpdate.emit("Opened SerialPort on port "+str(self.serialPort.portName()))
                self.openCloseButton.setText("Close")
                self.settings.setValue("portName", self.serialPort.portName())
                self.reopenTimer.stop()
                return True
            else:
                self.openCloseButton.setText("Open")
                return False

    def _closeSerialPort(self):
        self.serialPort.close()
        self.openCloseButton.setText("Open")

    def openCloseSwitch(self):
        # open or close the port
        if self.serialPort.isOpen():
            self._closeSerialPort()
            self.statusUpdate.emit("Closed SerialPort on port "+str(self.serialPort.portName()))
        else:
            if not self._openSerialPort():
                self.statusUpdate.emit("Can't open SerialPort on port "+str(self.serialPort.portName())+"!")

    def portChanged(self, portName):
        self.statusUpdate.emit("switching to serial port " + portName)
        if self.serialPort.isOpen():
            self.serialPort.close()
        self.serialPort.setPortName(portName)
        self.name = self.base_name + " " + self.serialPort.portName()
        self.statusLabel.setText(self.name)
        self.openCloseSwitch()

    def selectPort(self):
        d = SerialportDialog.SelectSerialportDialog()
        d.portChanged.connect(self.portChanged)
        d.exec_()

    def start(self):
        self.openCloseSwitch()

    def gotRxError(self, errType):
        print("RX " + errType)
        sys.stdout.flush()

    def stop(self):
        pass


class SerialConnection(BaseSerialConnection):
    def __init__(self, hdr, portName):
        super(SerialConnection, self).__init__("Serial", portName)

        self.hdr = hdr
        
        self.hdrTranslator = HeaderTranslator(hdr, Messaging.hdr)

        serialStartSeqField = Messaging.findFieldInfo(hdr.fields, "StartSequence")
        if serialStartSeqField != None:
            self.startSequence = int(hdr.GetStartSequence.default)
        else:
            self.startSequence = None
        try:
            self.hdrCrcRegion = int(hdr.GetHeaderChecksum.offset)
        except AttributeError:
            self.hdrCrcRegion = None
        self.tmpRxHdr = None

    def headerValid(self, hdr):
        if self.startSequence != None and hdr.GetStartSequence() != self.startSequence:
            #self.gotRxError("  HDR SS %s != %s" % (hex(hdr.GetStartSequence()) , hex(self.startSequence)))
            return False
        if self.hdrCrcRegion != None:
            # Stop computing before we reach header checksum location.
            headerCrc = Crc16(hdr.rawBuffer()[:self.hdrCrcRegion])
            receivedHeaderCrc = hdr.GetHeaderChecksum()
            if headerCrc != receivedHeaderCrc:
                self.gotRxError("HEADER CRC %s != %s for %s" % (hex(headerCrc) , hex(receivedHeaderCrc), hexbytes(hdr)))
                return False
        return True
    
    def bodyValid(self, hdr, body):
        if hdr.GetDataLength() != len(body):
            self.gotRxError("BODY LENGTH %d != %d" % (hdr.GetDataLength() != len(body)))
            return False
        if self.hdrCrcRegion != None:
            bodyCrc = Crc16(body)
            receivedBodyCrc = hdr.GetBodyChecksum()
            if receivedBodyCrc != bodyCrc:
                self.gotRxError("BODY CRC %s != %s for %s" % (hex(receivedBodyCrc), hex(bodyCrc), hexbytes(body)))
                return False
        return True

    def onReadyRead(self):
        while self.serialPort.bytesAvailable() > 0:
            if not self.tmpRxHdr:
                if self.serialPort.bytesAvailable() < self.hdr.SIZE:
                    return
                while self.serialPort.bytesAvailable() >= self.hdr.SIZE:
                    rx_bytes = bytes(self.serialPort.peek(self.hdr.SIZE))
                    serialHdr = self.hdr(rx_bytes)
                    if self.headerValid(serialHdr):
                        # read now, because we only peeked before.
                        self.tmpRxHdr = self.hdr(self.serialPort.read(self.hdr.SIZE))
                        break
                    else:
                        throwAway = self.serialPort.read(1)

            if self.tmpRxHdr != None:
                bodylen = self.tmpRxHdr.GetDataLength()
                if self.serialPort.bytesAvailable() >= bodylen:
                    # allocate the serial message body, read from the serial port
                    msgBody = self.serialPort.read(bodylen)
                    
                    if self.bodyValid(self.tmpRxHdr, msgBody):
                        self.rxMsgCount+=1
                        self.SerialMsgSlot(self.tmpRxHdr, msgBody)
                    self.tmpRxHdr = None
                else:
                    break

    def SerialMsgSlot(self, serialHdr, body):
        networkMsg = self.hdrTranslator.translateHdrAndBody(serialHdr, body)
        self.messagereceived.emit(networkMsg)

    def sendMsg(self, networkMsg):
        serialMsg = self.hdrTranslator.translate(networkMsg)
        # if we can't translate the message, just return
        if serialMsg == None:
            return
        if self.hdrCrcRegion != None:
            # set header and body CRC
            serialMsg.SetHeaderChecksum(Crc16(serialMsg.rawBuffer()[:self.hdrCrcRegion]))
            serialMsg.SetBodyChecksum(Crc16(serialMsg.rawBuffer()[self.hdr.SIZE:]))
        if self.serialPort.isOpen():
            self.serialPort.write(serialMsg.rawBuffer().raw)
    
def PluginConnection(param=None):
    from SerialHeader import SerialHeader
    return SerialConnection(SerialHeader, param)

def PluginEnabled():
    try:
        from SerialHeader import SerialHeader
        return True
    except:
        return False

def BtPluginConnection(param=None):
    from BluetoothHeader import BluetoothHeader
    return SerialConnection(BluetoothHeader, param)

def BtPluginEnabled():
    try:
        from BluetoothHeader import BluetoothHeader
        return True
    except:
        return False

import collections
PluginInfo = collections.namedtuple('PluginInfo', ['name', 'enabled', 'connect_function'])
plugin_info = PluginInfo('Serial', PluginEnabled, PluginConnection)
bt_plugin_info = PluginInfo('Bluetooth Serial', BtPluginEnabled, BtPluginConnection)
