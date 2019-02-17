#!/usr/bin/env python3
from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QDateTime
from PyQt5.QtSerialPort import QSerialPort

from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderTranslator
from msgtools.server import SerialportDialog

import ctypes
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

        self.serialPort.readyRead.connect(self.onReadyRead)
        self.name = self.base_name + " " + self.serialPort.portName()

    def onDisconnected(self):
        self.disconnected.emit(self)

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

    def openCloseSwitch(self):
        # open or close the port
        if self.serialPort.isOpen():
            self.statusUpdate.emit("Closed SerialPort on port "+str(self.serialPort.portName()))
            self.serialPort.close()
            self.openCloseButton.setText("Open")
        else:
            if self.serialPort.open(QSerialPort.ReadWrite):
                self.statusUpdate.emit("Opened SerialPort on port "+str(self.serialPort.portName()))
                self.openCloseButton.setText("Close")
                self.settings.setValue("portName", self.serialPort.portName())
            else:
                self.statusUpdate.emit("Can't open SerialPort on port "+str(self.serialPort.portName())+"!")
                self.openCloseButton.setText("Open")
        self.name = self.base_name + " " + self.serialPort.portName()
        self.statusLabel.setText(self.name)

    def portChanged(self, portName):
        self.statusUpdate.emit("switching to serial port " + portName)
        if self.serialPort.isOpen():
            self.serialPort.close()
        self.serialPort.setPortName(portName)
        self.openCloseSwitch()

    def selectPort(self):
        d = SerialportDialog.SelectSerialportDialog()
        d.portChanged.connect(self.portChanged)
        d.exec_()

    def start(self):
        self.openCloseSwitch()

    def gotRxError(self, errType):
        print("Got rx error " + errType)
        sys.stdout.flush()

    def stop(self):
        pass


class SerialConnection(BaseSerialConnection):
    def __init__(self, hdr, portName):
        super(SerialConnection, self).__init__("Serial", portName)

        self.hdr = hdr
        
        self.rxBuffer = bytearray()
        self.gotHeader = 0

        self.hdrTranslator = HeaderTranslator(hdr, Messaging.hdr)

        self.serialStartSeqField = Messaging.findFieldInfo(hdr.fields, "StartSequence")
        if self.serialStartSeqField != None:
            self.startSequence = int(hdr.GetStartSequence.default)
            self.startSeqSize = int(hdr.GetStartSequence.size)
        try:
            self.hdrCrcRegion = int(hdr.GetHeaderChecksum.offset)
        except AttributeError:
            self.hdrCrcRegion = None
        self.tmpRxHdr = ctypes.create_string_buffer(0)

    def onReadyRead(self):
        while self.serialPort.bytesAvailable() > 0:
            if not self.gotHeader:
                if self.serialStartSeqField != None:
                    foundStart = 0
                    # Synchronize on start sequence, if it exists
                    while self.serialPort.bytesAvailable() > 0 and self.serialPort.bytesAvailable() >= self.startSeqSize:
                        # peek at start of message.
                        #if it's start sequence, break.
                        #else, throw it away and try again.
                        self.tmpRxHdr = self.serialPort.peek(self.startSeqSize)
                        serialHdr = self.hdr(self.tmpRxHdr)
                        startSequence = serialHdr.GetStartSequence()
                        if startSequence == self.startSequence:
                            foundStart = 1
                            break
                        else:
                            print("  " + hex(startSequence) + " != " + hex(self.startSequence))
                            throwAway = self.serialPort.read(1)
                            #self.gotRxError("START")
                else:
                    foundStart = 1

                if foundStart:
                    if self.serialPort.bytesAvailable() >= self.hdr.SIZE:
                        self.tmpRxHdr = self.serialPort.read(self.hdr.SIZE)
                        serialHdr = self.hdr(self.tmpRxHdr)
                        if self.serialStartSeqField == None or serialHdr.GetStartSequence() == self.startSequence:
                            if self.hdrCrcRegion != None:
                                # Stop counting before we reach header checksum location.
                                headerCrc = Crc16(self.tmpRxHdr[:self.hdrCrcRegion])
                                receivedHeaderCrc = serialHdr.GetHeaderChecksum()
                                if headerCrc == receivedHeaderCrc:
                                    self.gotHeader = 1
                                else:
                                    #self.gotRxError("HEADER")
                                    print("  " + hex(headerCrc) + " != " + hex(receivedHeaderCrc))
                            else:
                                self.gotHeader = 1
                        else:
                            self.gotRxError("START")
                            print("Error in serial parser.  Thought I had start sequence, now it's gone!")
                    else:
                        break
                else:
                    break

            if self.gotHeader:
                serialHdr = self.hdr(self.tmpRxHdr)
                if self.serialPort.bytesAvailable() >= serialHdr.GetDataLength():
                    # allocate the serial message body, read from the serial port
                    bodylen = serialHdr.GetDataLength()
                    msgBody = self.serialPort.read(bodylen);

                    if self.hdrCrcRegion != None:
                        bodyCrc = Crc16(msgBody)
                        receivedBodyCrc = serialHdr.GetBodyChecksum()

                        if receivedBodyCrc != bodyCrc:
                            self.gotHeader = 0
                            self.gotRxError("BODY")
                        else:
                            self.gotHeader = 0
                            self.rxMsgCount+=1
                            self.SerialMsgSlot(serialHdr, msgBody)
                    else:
                        self.gotHeader = 0
                        self.rxMsgCount+=1
                        self.SerialMsgSlot(serialHdr, msgBody)
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
            serialMsg.SetBodyChecksum(Crc16(serialMsg.rawBuffer()[Messaging.hdrSize:]))
        if self.serialPort.isOpen():
            self.serialPort.write(serialMsg.rawBuffer().raw)
    
def PluginConnection(param=None):
    from SerialHeader import SerialHeader
    return SerialConnection(SerialHeader, param)

def BtPluginConnection(param=None):
    from BluetoothHeader import BluetoothHeader
    return SerialConnection(BluetoothHeader, param)
