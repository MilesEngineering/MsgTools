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

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

from Messaging import Messaging

class MsgApp(QMainWindow):
    RxMsg = Signal(bytearray)
    
    def __init__(self, name, headerName, argv):
        self.name = name
        
        # error out unless python version 3
        exit
        
        # rx buffer, to receive a message with multiple signals
        self.rxBuf = bytearray()
        
        self.allowedMessages = []
        self.keyFields = {}

        # need better handling of command line arguments for case when there is only one arg and it's a filename
        if(len(argv) == 3 and argv[2].lower().endswith((".txt",".log"))):
            self.connectionType = "file"
            self.connectionName = argv[2]
        else:
            optlist, args = getopt.getopt(sys.argv[1:], '', ['connectionType=', 'connectionName=', 'msg='])
            # connection modes
            self.connectionType = "qtsocket"
            self.connectionName = "127.0.0.1:5678"

            for opt in optlist:
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
        self.readFn = None

        srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
        msgdir = srcroot+"/../obj/CodeGenerator/Python/"
        self.msgLib = Messaging(msgdir, 0, headerName)
        
        self.status = QLabel("Initializing")
        self.statusBar().addPermanentWidget(self.status)

        self.OpenConnection()
        print("end of MsgApp.__init__")

    # this function opens a connection, and returns the connection object.
    def OpenConnection(self):
        print("\n\ndone reading message definitions, opening the connection ", self.connectionType, " ", self.connectionName)

        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            connectAction = QAction('&Connect', self)
            disconnectAction = QAction('&Disconnect', self)

            menubar = self.menuBar()
            connectMenu = menubar.addMenu('&Connect')
            connectMenu.addAction(connectAction)
            connectMenu.addAction(disconnectAction)

            (ip, port) = self.connectionName.split(":")
            if(ip == None):
                ip = "127.0.0.1"

            if(port == None):
                port = "5678"
            
            port = int(port)

            print("ip is ", ip, ", port is ", port)
            if(self.connectionType.lower() == "socket"):
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connected.connect(self.onConnected)
                self.connection.disconnected.connect(self.onDisconnect)
                self.readFn = self.connection.recv
                self.sendFn = self.connection.write
                self.connection.connect((ip, int(port)))
                connectAction.triggered.connect(self.chooseHost)
                disconnectAction.triggered.connect(self.connection.disconnect)
                # die "Could not create socket: $!\n" unless $connection
            elif(self.connectionType.lower() == "qtsocket"):
                self.connection = QTcpSocket(self)
                self.connection.error.connect(self.displayError)
                ret = self.connection.readyRead.connect(self.readRxBuffer)
                self.connection.connectToHost(ip, port)
                connectAction.triggered.connect(self.chooseHost)
                disconnectAction.triggered.connect(self.connection. disconnectFromHost)
                self.readFn = self.connection.read
                self.sendFn = self.connection.write
                #print("making connection returned", ret, "for socket", self.connection)
                self.connection.connected.connect(self.onConnected)
                self.connection.disconnected.connect(self.onDisconnect)
            else:
                print("\nERROR!\nneed to specify sockets of type 'socket' or 'qtsocket'")
                sys.exit()
            
        elif(self.connectionType.lower() == "file"):
            try:
                self.connection = open(self.connectionName, 'rb')
            except IOError:
                print("\nERROR!\ncan't open file ", self.connectionName)
            self.readFn = self.connection.read
            self.sendFn = self.connection.write
        else:
            print("\nERROR!\nneed to specify socket or file")
            sys.exit()

        self.connection;
    
    def chooseHost(self):
        (hostIp, port) = self.connectionName.split(":")
        if(hostIp == None):
            hostIp = "127.0.0.1"

        if(port == None):
            port = "5678"
        
        port = int(port)

        hostIp, ok = QInputDialog.getText(self, 'Connect',  'Server:', QLineEdit.Normal, hostIp)
        if(self.connectionType.lower() == "socket"):
            self.connection.connect(hostIp, int(port))
        elif(self.connectionType.lower() == "qtsocket"):
            self.connection.connectToHost(hostIp, port)
    
    def onConnected(self):
        # send a connect message
        connectBuffer = self.msgLib.Connect.Connect.Create();
        self.msgLib.Connect.Connect.SetName(connectBuffer, self.name);
        output_stream = QDataStream(self.connection)
        self.sendFn(connectBuffer.raw);
        self.status.setText('Connected')
    
    def onDisconnect(self):
        self.status.setText('*NOT* Connected')
    
    #
    def displayError(self, socketError):
        self.status.setText('Not Connected('+str(socketError)+')')
        print("Socket Error: " + str(socketError))

    # Qt signal/slot based reading of TCP socket
    @Slot(str)
    def readRxBuffer(self):
        input_stream = QDataStream(self.connection)
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
            
            # need to decode body len to read the body
            bodyLen = Messaging.hdr.GetLength(self.rxBuf)
            
            # read the body, unless we have the body
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                #print("reading", Messaging.hdrSize + bodyLen - len(self.rxBuf), "bytes for body")
                self.rxBuf += input_stream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuf))
            
            # if we still don't have the body, break
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                print("don't have full body, quitting")
                return
            
            # if we got this far, we have a whole message! So, emit the signal
            self.RxMsg.emit(self.rxBuf)
            # then clear the buffer, so we start over on the next message
            self.rxBuf = bytearray()

# this function reads messages, and calls the message handler.
    def MessageLoop(self):
        msgCount=0
        startSequence=0xDEADBEEF
        try:
            while (1):
                msgCount+=1
                self.rxBuf = self.readFn(Messaging.hdrSize)
                
                if(len(self.rxBuf) != Messaging.hdrSize):
                    raise StopIteration
                
                try:
                    start = Messaging.hdr.GetStartSequence(self.rxBuf)
                    if(start != startSequence):
                        print("Error on message " + str(msgCount) + ". Start sequence invalid: 0x" + format(start, '02X'))
                        # resync on start sequence
                        bytesThrownAway = 0
                        while (1):
                            self.rxBuf += self.readFn(1)
                            self.rxBuf = self.rxBuf[1:]
                            if(len(self.rxBuf) != Messaging.hdrSize):
                                raise StopIteration
                            bytesThrownAway += 1
                            start = Messaging.hdr.GetStartSequence(self.rxBuf)
                            if(start == startSequence):
                                print("Resynced after " + str(bytesThrownAway) + " bytes")
                                break
                    headerChecksum = Messaging.hdr.GetHeaderChecksum(self.rxBuf)
                    bodyChecksum = Messaging.hdr.GetBodyChecksum(self.rxBuf)
                except AttributeError:
                    pass

                # need to decode body len to read the body
                bodyLen = Messaging.hdr.GetLength(self.rxBuf)
                
                # read the body
                self.rxBuf += self.readFn(bodyLen)
                if(len(self.rxBuf) != Messaging.hdrSize + bodyLen): break

                # got a complete message, call the callback to process it
                self.PrintMessage(self.rxBuf)
        except StopIteration:
            print("found end of file, exited")
