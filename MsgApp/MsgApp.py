import socket

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

from Messaging import Messaging

class MsgApp(QMainWindow):
    RxMsg = Signal(QByteArray, QObject)
    
    def __init__(self, msgdir, name, argv):
        self.name = name
        
        # rx buffer, to receive a message with multiple signals
        self.rxBuf = ""
        
        # connection modes
        self.connectionType = "qtsocket"
        self.connectionName = "127.0.0.1:5678"

        if(len(argv) > 1):
            self.connectionType = argv[1]
        if(len(argv) > 2):
            self.connectionName = argv[2]
        
        # initialize the read function to None, so it's not accidentally called
        self.readFn = None

        self.msgLib = Messaging(msgdir, 0)

        self.OpenConnection()
        print("end of MsgApp.__init__")

    # this function opens a connection, and returns the connection object.
    def OpenConnection(self):
        print("\n\ndone reading message definitions, opening the connection ", self.connectionType, " ", self.connectionName)

        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            (ip, port) = self.connectionName.split(":")
            if(ip == None):
                ip = "127.0.0.1"

            if(port == None):
                port = "5678"
            
            port = int(port)

            print("ip is ", ip, ", port is ", port)
            if(self.connectionType.lower() == "socket"):
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((ip, int(port)))
                # die "Could not create socket: $!\n" unless $connection
                self.readFn = self.connection.recv
                self.sendFn = self.connection.write
            elif(self.connectionType.lower() == "qtsocket"):
                self.connection = QTcpSocket(self)
                self.connection.error.connect(self.displayError)
                ret = self.connection.readyRead.connect(self.readRxBuffer)
                #print("making connection returned", ret, "for socket", self.connection)
                self.connection.connectToHost(ip, port)
                self.readFn = self.connection.read
                self.sendFn = self.connection.write
            else:
                print("\nERROR!\nneed to specify sockets of type 'socket' or 'qtsocket'")
                sys.exit()
            # send a connect message
            connectBuffer = self.msgLib.Connect.Connect.Create();
            self.msgLib.Connect.Connect.SetName(connectBuffer, self.name);
            output_stream = QDataStream(self.connection)
            self.sendFn(connectBuffer.raw);
            
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
    
    #
    def displayError(self, socketError):
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
            bodyLen = Messaging.hdr.GetLength(rxBuf)
            
            # read the body, unless we have the body
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                #print("reading", Messaging.hdrSize + bodyLen - len(self.rxBuf), "bytes for body")
                self.rxBuf += input_stream.readRawData(Messaging.hdrSize + bodyLen - len(self.rxBuf))
            
            # if we still don't have the body, break
            if(len(self.rxBuf) < Messaging.hdrSize + bodyLen):
                print("don't have full body, quitting")
                return
            
            # if we got this far, we have a whole message! So, emit the signal
            self.RxMsg.emit(QByteArray(self.rxBuf), self)
            # then clear the buffer, so we start over on the next message
            self.rxBuf = ''

    # this function reads messages, and calls the message handler.
    def MessageLoop(self, ProcessMessage):
        while (1):
            self.rxBuf = self.readFn(Messaging.hdrSize)
            
            if(len(self.rxBuf) != Messaging.hdrSize): break

            # need to decode body len to read the body
            bodyLen = Messaging.hdr.GetLength(rxBuf)
            
            # read the body
            self.rxBuf += self.readFn(bodyLen)
            if(len(self.rxBuf) != Messaging.hdrSize + bodyLen): break

            # got a complete message, call the callback to process it
            ProcessMessage(self.rxBuf, self)
