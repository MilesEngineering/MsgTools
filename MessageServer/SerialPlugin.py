#!/usr/bin/env python3
from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QDateTime
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtSerialPort import QSerialPort

from Messaging import *

from NetworkHeader import NetworkHeader

import ctypes

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

def findFieldInfo(fieldInfos, name):
    for fi in fieldInfos:
        if len(fi.bitfieldInfo) == 0:
            if name == fi.name:
                return fi
        else:
            for bfi in fi.bitfieldInfo:
                if name == bfi.name:
                    return bfi
    return None
    
class SerialConnection(QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)
    startTime = QDateTime.currentDateTime()

    def __init__(self, hdr, portName):
        super(SerialConnection, self).__init__(None)

        self.hdr = hdr
        
        self.pushButton = QtWidgets.QPushButton("button")
        self.pushButton.pressed.connect(self.onButtonPress)
        self.statusLabel = QtWidgets.QLabel()
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0

        self.portName = portName
        self.serialPort = QSerialPort(portName)
        self.serialPort.setBaudRate(QSerialPort.Baud115200);
        self.serialPort.setFlowControl(QSerialPort.NoFlowControl);
        self.serialPort.setParity(QSerialPort.NoParity);
        self.serialPort.setDataBits(QSerialPort.Data8);
        self.serialPort.setStopBits(QSerialPort.OneStop);
        self.rxBuffer = bytearray()
        self.gotHeader = 0
        self.rxMsgCount = 0

        self.serialPort.readyRead.connect(self.onReadyRead)
        self.name = "Serial " + self.portName
        self.statusLabel.setText(self.name)

        # Make a list of fields in the serial header and network header that have matching names.
        self.correspondingFields = []
        for serialFieldInfo in hdr.fields:
            if len(serialFieldInfo.bitfieldInfo) == 0:
                nfi = findFieldInfo(NetworkHeader.fields, serialFieldInfo.name)
                if nfi != None:
                    self.correspondingFields.append([serialFieldInfo, nfi])
            else:
                for serialBitfieldInfo in serialFieldInfo.bitfieldInfo:
                    nfi = findFieldInfo(NetworkHeader.fields, serialBitfieldInfo.name)
                    if nfi != None:
                        self.correspondingFields.append([serialBitfieldInfo, nfi])

        self.serialStartSeqField = findFieldInfo(hdr.fields, "StartSequence")
        if self.serialStartSeqField != None:
            self.startSequence = int(hdr.GetStartSequence.default)
            self.startSeqSize = int(hdr.GetStartSequence.size)
        try:
            self.hdrCrcRegion = int(hdr.GetHeaderChecksum.offset)
        except AttributeError:
            self.hdrCrcRegion = None
        self.serialTimeField = findFieldInfo(hdr.fields, "Time")
        self.networkTimeField = findFieldInfo(NetworkHeader.fields, "Time")
        self.tmpRxHdr = ctypes.create_string_buffer(0)

    def widget(self, index):
        if index == 0:
            return self.pushButton
        if index == 1:
            return self.statusLabel
        return None

    def onButtonPress(self):
        # open or close the port
        if self.serialPort.isOpen():
            self.statusUpdate.emit("Closed SerialPort on port "+str(self.portName))
            self.serialPort.close()
            self.pushButton.setText("Open")
        else:
            if self.serialPort.open(QSerialPort.ReadWrite):
                self.statusUpdate.emit("Opened SerialPort on port "+str(self.portName))
                self.pushButton.setText("Close")
            else:
                self.statusUpdate.emit("Can't open SerialPort on port "+str(self.portName)+"!")
                self.pushButton.setText("Open")

    def start(self):
        if self.serialPort.open(QSerialPort.ReadWrite):
            self.statusUpdate.emit("Opened SerialPort on port "+str(self.portName))
            self.pushButton.setText("Close")
        else:
            self.statusUpdate.emit("Can't open SerialPort on port "+str(self.portName)+"!")
            self.pushButton.setText("Open")

    def gotRxError(self, errType):
        print("Got rx error " + errType)
        sys.stdout.flush()

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
                        startSequence = self.hdr.GetStartSequence(self.tmpRxHdr)
                        if startSequence == self.startSequence:
                            foundStart = 1
                            break;
                        else:
                            print("  " + hex(startSequence) + " != " + hex(self.startSequence))
                            throwAway = self.serialPort.read(1)
                            #self.gotRxError("START")
                else:
                    foundStart = 1

                if foundStart:
                    if self.serialPort.bytesAvailable() >= self.hdr.SIZE:
                        self.tmpRxHdr = self.serialPort.read(self.hdr.SIZE)
                        if self.serialStartSeqField == None or self.hdr.GetStartSequence(self.tmpRxHdr) == self.startSequence:
                            if self.hdrCrcRegion != None:
                                # Stop counting before we reach header checksum location.
                                headerCrc = Crc16(self.tmpRxHdr[:self.hdrCrcRegion])
                                receivedHeaderCrc = self.hdr.GetHeaderChecksum(self.tmpRxHdr)
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
                if self.serialPort.bytesAvailable() >= self.hdr.GetDataLength(self.tmpRxHdr):
                    # allocate the serial message body, read from the serial port
                    bodylen = self.hdr.GetDataLength(self.tmpRxHdr)
                    msgBody = self.serialPort.read(bodylen);

                    if self.hdrCrcRegion != None:
                        bodyCrc = Crc16(msgBody)
                        receivedBodyCrc = self.hdr.GetBodyChecksum(self.tmpRxHdr)

                        if receivedBodyCrc != bodyCrc:
                            self.gotHeader = 0
                            self.gotRxError("BODY")
                        else:
                            self.gotHeader = 0
                            self.rxMsgCount+=1
                            self.SerialMsgSlot(self.tmpRxHdr, msgBody)
                    else:
                        self.gotHeader = 0
                        self.rxMsgCount+=1
                        self.SerialMsgSlot(self.tmpRxHdr, msgBody)
                else:
                    break

    def SerialMsgSlot(self, serialHdr, body):
        dbmsg = ctypes.create_string_buffer(NetworkHeader.SIZE+self.hdr.GetDataLength(serialHdr))
        NetworkHeader.SetMessageID(dbmsg, self.hdr.GetMessageID(serialHdr))

        # loop through fields using reflection, and transfer contents from
        # serial message to network message
        for pair in self.correspondingFields:
            si = pair[0]
            ni = pair[1]
            value = Messaging.get(serialHdr, si)
            Messaging.set(dbmsg, ni, Messaging.get(serialHdr, si))

        if self.serialTimeField != None and self.networkTimeField != None and self.serialTimeFieldSize < self.networkTimeFieldSize:
            # Detect time rolling
            thisTimestamp = self.hdr.GetTime(serialHdr)
            thisTime = QDateTime.currentDateTime()
            timestampOffset = self.timestampOffset
            if thisTimestamp < self.lastTimestamp:
                # If the timestamp shouldn't have wrapped yet, assume messages sent out-of-order,
                # and do not wrap again.
                if thisTime > self.lastWrapTime.addSecs(30):
                    self.lastWrapTime = thisTime
                    self.timestampOffset+=1
                    timestampOffset = self.timestampOffset
            self.lastTimestamp = thisTimestamp
            NetworkHeader.SetTime(dbmsg, (timestampOffset << 16) + thisTimestamp)
        elif self.networkTimeField != None and self.serialTimeField == None:
            thisTime = QDateTime.currentDateTime()
            NetworkHeader.SetTime(dbmsg, self.startTime.msecsTo(thisTime))

        for i in range(0,len(body)):
            dbmsg[NetworkHeader.SIZE+i] = body[i]
        self.messagereceived.emit(dbmsg.raw)

    def sendMsg(self, msg):
        bodyLen = Messaging.hdr.GetDataLength(msg)
        serialHdr = self.hdr.Create()
        #set hdr fields that exist in network and serial
        for pair in self.correspondingFields:
            si = pair[0]
            ni = pair[1]
            Messaging.set(serialHdr, si, Messaging.get(msg, ni))
        if self.hdrCrcRegion != None:
            # set header and body CRC
            self.hdr.SetHeaderChecksum(serialHdr, Crc16(serialHdr[:self.hdrCrcRegion]))
            self.hdr.SetBodyChecksum(serialHdr, Crc16(msg[Messaging.hdrSize:]))
        self.serialPort.write(serialHdr.raw)
        self.serialPort.write(msg[Messaging.hdrSize:])
