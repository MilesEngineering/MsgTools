import socket
import os
import sys
import getopt

if sys.version_info<(3,4):
    raise SystemExit('''\n\nSorry, this code need Python 3.4 or higher.\n
To avoid incorrectly using python2 in your path, you may want to try launching by:
    ./path/to/script/ScriptName.py
NOT
    python path/to/script/ScriptName.py\n''')

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork
from PyQt5.QtWidgets import QInputDialog, QLineEdit

from .messaging import Messaging

class App(QtWidgets.QMainWindow):
    RxMsg = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)
    connectionChanged = QtCore.pyqtSignal(bool)
    
    def __init__(self, name, headerName, argv, options):
        self.name = name
        
        # persistent settings
        self.settings = QtCore.QSettings("MsgTools", name)
        
        # rx buffer, to receive a message with multiple signals
        self.rxBuf = bytearray()
        
        self.allowedMessages = []
        self.keyFields = {}

        # need better handling of command line arguments for case when there is only one arg and it's a filename
        if(len(argv) == 3 and argv[2].lower().endswith((".txt",".log"))):
            self.connectionType = "file"
            self.connectionName = argv[2]
        else:
            allOptions = options
            options += ['connectionType=', 'connectionName=', 'msg=']
            self.optlist, args = getopt.getopt(sys.argv[1:], '', allOptions)
            # connection modes
            self.connectionType = "qtsocket"
            self.connectionName = "127.0.0.1:5678"

            for opt in self.optlist:
                if opt[0] == '--connectionType':
                    self.connectionType = opt[1]
                if opt[0] == '--connectionName':
                    self.connectionName = opt[1]
                if opt[0] == '--msg':
                    option = opt[1].split('/')
                    self.allowedMessages.append(option[0])
                    if len(option) > 1:
                        self.keyFields[option[0]] = option[1]
                    print("only allowing msg " + str(option))
        
        # initialize the read function to None, so it's not accidentally called
        self.readBytesFn = None

        self.msgLib = Messaging(None, 0, headerName)
        
        self.OpenConnection()

    # this function opens a connection, and returns the connection object.
    def OpenConnection(self):
        #print("\n\ndone reading message definitions, opening the connection ", self.connectionType, " ", self.connectionName)

        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            (ip, port) = self.connectionName.split(":")
            if(ip == None):
                ip = "127.0.0.1"

            if(port == None):
                port = "5678"
            
            port = int(port)

            #print("ip is ", ip, ", port is ", port)
            self.connection = QtNetwork.QTcpSocket(self)
            self.connection.error.connect(self.displayConnectError)
            ret = self.connection.readyRead.connect(self.readRxBuffer)
            self.connection.connectToHost(ip, port)
            self.readBytesFn = self.connection.read
            self.sendBytesFn = self.connection.write
            #print("making connection returned", ret, "for socket", self.connection)
            self.connection.connected.connect(self.onConnected)
            self.connection.disconnected.connect(self.onDisconnect)
            
        elif(self.connectionType.lower() == "file"):
            try:
                self.connection = open(self.connectionName, 'rb')
            except IOError:
                print("\nERROR!\ncan't open file ", self.connectionName)
            self.readBytesFn = self.connection.read
            self.sendBytesFn = self.connection.write
        else:
            print("\nERROR!\nneed to specify socket or file")
            sys.exit()

        self.connection;
    
    def onConnected(self):
        self.connectionChanged.emit(True)
        # send a connect message
        connectMsg = self.msgLib.Messages.Network.Connect()
        connectMsg.SetName(self.name)
        self.SendMsg(connectMsg)
        # if the app has it's own function to happen after connection, assume it will set subscriptions to what it wants.
        try:
            fn = self.onAppConnected
        except AttributeError:
            # send a subscription message
            subscribeMsg = self.msgLib.Messages.Network.MaskedSubscription()
            self.SendMsg(subscribeMsg)
            #self.statusUpdate.emit('Connected')
        else:
            self.onAppConnected()
    
    def onDisconnect(self):
        self.connectionChanged.emit(False)
        #self.statusUpdate.emit('NOT Connected')
    
    def displayConnectError(self, socketError):
        self.connectionChanged.emit(False)
        self.statusUpdate.emit('Not Connected('+str(socketError)+'), '+self.connection.errorString())

    # Qt signal/slot based reading of TCP socket
    def readRxBuffer(self):
        input_stream = QtCore.QDataStream(self.connection)
        while(self.connection.bytesAvailable() > 0):
            # read the header, unless we have the header
            if(len(self.rxBuf) < Messaging.hdrSize):
                #print("reading", Messaging.hdrSize - len(self.rxBuf), "bytes for header")
                self.rxBuf += input_stream.readRawData(Messaging.hdrSize - len(self.rxBuf))
                #print("have", len(self.rxBuf), "bytes")
            
            # if we still don't have the header, break
            if(len(self.rxBuf) < Messaging.hdrSize):
                print("don't have full header, quitting")
                return
            
            hdr = Messaging.hdr(self.rxBuf)
            
            # need to decode body len to read the body
            bodyLen = hdr.GetDataLength()
            
            # read the body, unless we have the body
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                #print("reading", Messaging.hdrSize + bodyLen - len(self.rxBuf), "bytes for body")
                self.rxBuf += input_stream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuf))
            
            # if we still don't have the body, break
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                print("don't have full body, quitting")
                return
            
            # if we got this far, we have a whole message! So, emit the signal
            self.RxMsg.emit(Messaging.MsgFactory(hdr))
            # then clear the buffer, so we start over on the next message
            self.rxBuf = bytearray()
    
    def SendMsg(self, msg):
        bufferSize = len(msg.rawBuffer().raw)
        hdr = msg.hdr
        computedSize = Messaging.hdrSize + hdr.GetDataLength()
        if(computedSize > bufferSize):
            hdr.SetDataLength(bufferSize - Messaging.hdrSize)
            print("Truncating message to "+str(computedSize)+" bytes")
        if(computedSize < bufferSize):
            # don't send the *whole* message, just a section of it up to the specified length
            self.sendBytesFn(msg.rawBuffer().raw[0:computedSize])
        else:
            self.sendBytesFn(msg.rawBuffer().raw)

    # this function reads messages (perhaps from a file, like in LumberJack), and calls the message handler.
    # unclear if it ever makes sense to use this in a application that talks to a socket or UART, because
    # it exits when there's no more data.  Perhaps it does in a CLI that's very procedural, like an automated
    # system test script?
    def MessageLoop(self):
        msgCount=0
        startSeqField = Messaging.findFieldInfo(Messaging.hdr.fields, "StartSequence")
        if startSeqField == None:
            print("header contains no StartSequence")
        else:
            startSequence = int(Messaging.hdr.GetStartSequence.default)
            print("header contains StartSequence " + hex(startSequence))
        try:
            while (1):
                msgCount+=1
                self.rxBuf = self.readBytesFn(Messaging.hdrSize)
                
                if(len(self.rxBuf) != Messaging.hdrSize):
                    raise StopIteration
                
                hdr = Messaging.hdr(self.rxBuf)
                try:
                    start = hdr.GetStartSequence()
                    if(start != startSequence):
                        print("Error on message " + str(msgCount) + ". Start sequence invalid: 0x" + format(start, '02X'))
                        # resync on start sequence
                        bytesThrownAway = 0
                        while (1):
                            self.rxBuf += self.readBytesFn(1)
                            self.rxBuf = self.rxBuf[1:]
                            if(len(self.rxBuf) != Messaging.hdrSize):
                                raise StopIteration
                            bytesThrownAway += 1
                            start = hdr.GetStartSequence()
                            if(start == startSequence):
                                print("Resynced after " + str(bytesThrownAway) + " bytes")
                                break
                    headerChecksum = hdr.GetHeaderChecksum()
                    bodyChecksum = hdr.GetBodyChecksum(self)
                except AttributeError:
                    pass

                # need to decode body len to read the body
                bodyLen = hdr.GetDataLength()
                
                # read the body
                self.rxBuf += self.readBytesFn(bodyLen)
                if(len(self.rxBuf) != Messaging.hdrSize + bodyLen): break
                
                hdr = Messaging.hdr(self.rxBuf)

                # got a complete message, call the callback to process it
                self.ProcessMessage(Messaging.MsgFactory(hdr))
        except StopIteration:
            print("found end of file, exited")
