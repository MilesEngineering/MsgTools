# for socket recv
import socket
# for qt socket stuff
from PySide import QtCore, QtGui, QtNetwork

class MsgApp(QtGui.QMainWindow):
    RxMsg = QtCore.Signal(QtCore.QByteArray, QtCore.QObject)
    
    def __init__(self, msgdir, name, argv, parent=None):
        # call base class init
        QtGui.QMainWindow.__init__(self,parent)
        self.name = name
        
        # rx buffer, to receive a message with multiple signals
        self.rxBuf = ''
        
        if(len(argv) > 1):
            connectionType = argv[1]
        else:
            connectionType = "qtsocket"
        if(len(argv) > 2):
            connectionName = argv[2]
        else:
            connectionName = "127.0.0.1:5678"
        
        # initialize the read function to None, so it's not accidentally called
        self.readFn = None

        label = QtGui.QLabel("<font size=40>Some Text</font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)

        import Messaging
        self.msgLib = Messaging.Messaging(msgdir, 0)

        self.OpenConnection(connectionType, connectionName)
        print("end of MsgApp.__init__")

    # this function opens a connection, and returns the connection object.
    def OpenConnection(self, connectionType=None, connectionName=None):
        print("\n\ndone reading message definitions, opening the connection ", connectionType, " ", connectionName)
        if(connectionType is None):
            connectionType = "socket"

        if(connectionType.lower() == "socket" or connectionType.lower() == "qtsocket"):
            if(connectionName != None):
                (ip, port) = connectionName.split(":")
                if(ip == None):
                    ip = "127.0.0.1"

                if(port == None):
                    port = "5678"
            else:
                (ip, port) = ("127.0.0.1", "5678")
            
            port = int(port)

            print("ip is ", ip, ", port is ", port)
            if(connectionType.lower() == "socket"):
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((ip, int(port)))
                # die "Could not create socket: $!\n" unless $connection
                self.readFn = self.connection.recv
            elif(connectionType.lower() == "qtsocket"):
                self.connection = QtNetwork.QTcpSocket(self)
                self.connection.error.connect(self.displayError)
                ret = self.connection.readyRead.connect(self.readRxBuffer)
                #print("making connection returned", ret, "for socket", self.connection)
                self.connection.connectToHost(ip, port)
                self.readFn = self.connection.read
            else:
                print("\nERROR!\nneed to specify sockets of type 'socket' or 'qtsocket'")
                sys.exit()
        elif(connectionType.lower() == "file"):
            try:
                self.connection = open(connectionName, 'rb')
            except IOError:
                print("\nERROR!\ncan't open file ", connectionName)
            self.readFn = self.connection.read
        else:
            print("\nERROR!\nneed to specify socket or file")
            sys.exit()

        self.connection;
    
    #
    def displayError(self, socketError):
        print("got error")

    # Qt signal/slot based reading of TCP socket
    @QtCore.Slot(str)
    def readRxBuffer(self):
        #print("readRxBuffer")
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
            self.RxMsg.emit(QtCore.QByteArray(self.rxBuf), self)
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
