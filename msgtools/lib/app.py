import socket
import os
import sys
import argparse

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

    @classmethod
    def addBaseArguments(cls, parser):
        '''
        Adds base app arguments to the provided ArgParser
        skipFiles - if True we won't provide an agument for a files list
        returns the parser
        '''
        parser.add_argument('--connectionType', choices=['socket', 'qtsocket', 'file'], default='qtsocket',
            help='Specify the type of connection we are establishing as a message pipe/source.')
        parser.add_argument('--connectionName', default='127.0.0.1:5678',
            help='''The connection name.  For socket connections this is an IP and port e.g. 127.0.0.1:5678.  
                    You may prepend ws:// to indicate you want to use a Websocket instead.  For file 
                    connection types, this is the filename to use as a message source.
                    This parameter is overridden by the --ip and --port options.''')
        parser.add_argument('--ip', help='The IP address for a socket connection.   Overrides connectionName.')
        parser.add_argument('--port', type=int, help='The port for a socket connection. Overrides connectionName.')
        parser.add_argument('--msg', nargs='+', default=set(), help='''A space delimited list of white list messages to process.
                    All messages outside of this list will be ignored.  For example: --msg TestCase1 Network.Note 
                    Taxonomy/Candidae.AFox''')
        parser.add_argument('--msgdir', help=''''The directory to load Python message source from.''')
        parser.add_argument('--serial', action='store_true', help='Set if you want to use a SerialHeader instead of a NetworkHeader.')

        return parser
    
    def __init__(self, name, args):
        '''Initializer - this is used more as a decorator in the MsgTools suite than an actual
        standalone class.

        name - the name of the application - usually displayed in the UI window header
        args - argparse.Namespace of command line options.  See getArgParser for what we provide
               by default as part of this base app framework.  A command line tool may act as a 
               parent ArgumentParser and provide additional options.
        '''

        # If the caller skips adding base arguments we need to patch up args
        args.serial = None if hasattr(args, 'serial') == False else args.serial
        args.msg = None if hasattr(args, 'msg') == False else args.msg
        args.msgdir = None if hasattr(args, 'msgdir') == False else args.msgdir

        # default to Network, unless we have a input filename that contains .txt
        headerName = "NetworkHeader"
        if args.serial or (args.connectionType=='file' and os.path.splitext(args.connectionType)[1].lower() == '.txt'):
            headerName = "SerialHeader"

        self.name = name
        
        # persistent settings
        self.settings = QtCore.QSettings("MsgTools", name)
        
        # rx buffer, to receive a message with multiple signals
        self.rxBuf = bytearray()
        
        self.allowedMessages = set(args.msg)
        
        # flag that indicates if we're connected
        self.connected = False
        
        # directory to load messages from.
        msgLoadDir = None

        # connection modes
        ip = ""
        port = ""

        if args.connectionType is not None:
            self.connectionType = args.connectionType
        if args.connectionName is not None:
            self.connectionName = args.connectionName
        if args.ip is not None:
            ip = args.ip
        if args.msgdir:
            msgLoadDir = args.msgdir
        
        # if either --ip or --port were used, override connectionName
        if args.ip is not None or args.port is not None:
            self.connectionName = str(ip)+":"+str(port)
        
        # initialize the read function to None, so it's not accidentally called
        self.readBytesFn = None

        try:
            Messaging.LoadAllMessages(searchdir=msgLoadDir, headerName=headerName)

            if args.msg is not None:
                # Validate all message names are valid
                for msg in args.msg:
                    if msg not in Messaging.MsgIDFromName:
                        print('{0} is not a valid message name!'.format(msg))
                        sys.exit(1)
                port = args.port

        except ImportError:
            print("\nERROR! Auto-generated python code not found!")
            print("cd to a directory downstream from a parent of obj/CodeGenerator/Python")
            print("or specify that directory with --msgdir=PATH\n")
            quit()
        
        self.OpenConnection()

    def CloseConnection(self):
        if hasattr(self, 'connection') and (self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            if "ws:" in self.connectionName:
                if self.connection:
                    self.connection.close()
                    self.connection = None
            else:
                if self.connection:
                    self.connection.disconnectFromHost()
                    self.connection = None

    # this function opens a connection, and returns the connection object.
    def OpenConnection(self):
        self.CloseConnection()

        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            if "ws:" in self.connectionName:
                connectionName = self.connectionName.replace("ws://","")
                (ip, port) = connectionName.rsplit(":",1)
                if ip == None or ip == "":
                    ip = "127.0.0.1"

                if port == None or port == "":
                    port = "5679"
                connectionName = "ws://"+ip+":"+port
                from PyQt5.QtWebSockets import QWebSocket
                from PyQt5.QtCore import QUrl
                self.connection = QWebSocket()
                print("opening websocket " + connectionName)
                self.connection.open(QUrl(connectionName))
                self.connection.binaryMessageReceived.connect(self.processBinaryMessage)
                self.sendBytesFn = self.connection.sendBinaryMessage
            else:
                #print("opening TCP socket " + self.connectionName)
                (ip, port) = self.connectionName.rsplit(":",1)
                if ip == None or ip == "":
                    ip = "127.0.0.1"

                if port == None or port == "":
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
                self.readBytesFn = self.connection.read
                self.sendBytesFn = self.connection.write
            except IOError:
                print("\nERROR!\ncan't open file ", self.connectionName)
                sys.exit(1)
        else:
            print("\nERROR!\nneed to specify socket or file")
            sys.exit()

        self.connection;
    
    def onConnected(self):
        self.connected = True
        self.connectionChanged.emit(True)
        # send a connect message
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName(self.name)
        self.SendMsg(connectMsg)
        # if the app has it's own function to happen after connection, assume it will set subscriptions to what it wants.
        try:
            fn = self.onAppConnected
        except AttributeError:
            # send a subscription message
            subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
            self.SendMsg(subscribeMsg)
            #self.statusUpdate.emit('Connected')
        else:
            self.onAppConnected()
    
    def onDisconnect(self):
        self.connected = False
        self.connectionChanged.emit(False)
        #self.statusUpdate.emit('NOT Connected')
    
    def displayConnectError(self, socketError):
        self.connected = False
        self.connectionChanged.emit(False)
        self.statusUpdate.emit('Not Connected('+str(socketError)+'), '+self.connection.errorString())

    # Qt signal/slot based reading of websocket
    def processBinaryMessage(self, bytes):
        if isinstance(bytes, bytearray):
            hdr = Messaging.hdr(bytes)
        else:
            # Assume this is a QByteArray from a websocket
            hdr = Messaging.hdr(bytes.data())

        # if we got this far, we have a whole message! Emit the signal
        # if the message is whitelisted
        msg = Messaging.MsgFactory(hdr)
        if self._messageAllowed(msg):
            self.RxMsg.emit(msg)

    def _messageAllowed(self, msg):
        '''Check msg against the list of allowed messages.

        return True if all messages are allowed, or the message is
        in the message white list.'''
        retVal = True
        if len(self.allowedMessages) > 0:
            if not msg.MsgName() in self.allowedMessages:
                retVal = False

        return retVal

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

            # Process what we assume to be a full message...            
            self.processBinaryMessage(self.rxBuf)

            # then clear the buffer, so we start over on the next message
            self.rxBuf = bytearray()
    
    def SendMsg(self, msg):
        bufferSize = len(msg.rawBuffer().raw)
        computedSize = Messaging.hdrSize + msg.hdr.GetDataLength()
        if(computedSize > bufferSize):
            msg.hdr.SetDataLength(bufferSize - Messaging.hdrSize)
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
    #
    # Note: This loop won't work with Qt socket signals.  For signals to work you have to exeucute the
    # application event loop.  To make this method work with QtSockets you would need to layer in 
    # the various waitFor* methods on the connection within this loop.
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
                
                # create a new header object with the appended body
                hdr = Messaging.hdr(self.rxBuf)

                # got a complete message, call the callback to process it if
                # the message is on our white list
                msg = Messaging.MsgFactory(hdr)
                if self._messageAllowed(msg):
                    self.ProcessMessage(msg)
        except StopIteration:
            print("found end of file, exited")

