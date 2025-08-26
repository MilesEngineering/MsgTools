from PyQt5 import QtCore, QtNetwork
from .messaging import Messaging

# Used for TCP socket and websocket connections to a server.
class ClientConnection(QtCore.QObject):
    connection_error = QtCore.pyqtSignal(QtNetwork.QAbstractSocket.SocketError)
    on_connect = QtCore.pyqtSignal()
    on_disconnect = QtCore.pyqtSignal()
    rx_msg = QtCore.pyqtSignal(object)
    rx_hdr = QtCore.pyqtSignal(object)
    def __init__(self, header_class, name=None):
        super(ClientConnection, self).__init__(None)
        # initialize the read function to None, so it's not accidentally called
        self.readBytesFn = None
        # rx buffer, to receive a message with multiple reads
        self.rx_buf = bytearray()
        self.connection = None
        if name:
            self.OpenConnection(name)

    def OpenConnection(self, connection_name):
        self.CloseConnection()

        if "ws:" in connection_name:
            connection_name = connection_name.replace("ws://","")
            (ip, port) = connection_name.rsplit(":",1)
            if ip == None or ip == "":
                ip = "127.0.0.1"

            if port == None or port == "":
                port = "5679"
            connection_name = "ws://"+ip+":"+port
            from PyQt5.QtWebSockets import QWebSocket
            from PyQt5.QtCore import QUrl
            self.connection = QWebSocket()
            #print("opening websocket " + connection_name)
            self.connection.open(QUrl(connection_name))
            self.connection.binaryMessageReceived.connect(self._processBinaryMessage)
            self.sendBytesFn = self.connection.sendBinaryMessage
        else:
            #print("opening TCP socket %s" % (connection_name))
            (ip, port) = connection_name.rsplit(":",1)
            if ip == None or ip == "":
                ip = "127.0.0.1"

            if port == None or port == "":
                port = "5678"
            
            port = int(port)

            #print("OpenConnection(), connecting to %s %s" % (ip, port))
            self.connection = QtNetwork.QTcpSocket(self)
            self.connection.error.connect(self.connection_error)
            ret = self.connection.readyRead.connect(self._readRxBuffer)
            self.connection.connectToHost(ip, port)
            self.readBytesFn = self.connection.read
            self.sendBytesFn = self.connection.write
            #print("making connection returned", ret, "for socket", self.connection)
        self.connection.connected.connect(self.on_connect)
        self.connection.disconnected.connect(self.on_disconnect)

    def CloseConnection(self):
        if not self.connection:
            return

        try:
            self.connection.close()
        except:
            pass
        try:
            self.connection.disconnectFromHost()
        except:
            pass
        self.connection = None

    def SendHeader(self, hdr):
        self.sendBytesFn(hdr.rawBuffer().raw)

    def SendMsg(self, msg):
        bufferSize = len(msg.rawBuffer().raw)
        computedSize = Messaging.hdrSize + msg.hdr.GetDataLength()
        if(computedSize > bufferSize):
            msg.hdr.SetDataLength(bufferSize - Messaging.hdrSize)
            print("app.py: Truncating message %s from %d to %d bytes" % (msg.__class__.__name__, computedSize, bufferSize))
        if(computedSize < bufferSize):
            # don't send the *whole* message, just a section of it up to the specified length
            self.sendBytesFn(msg.rawBuffer().raw[0:computedSize])
        else:
            self.sendBytesFn(msg.rawBuffer().raw)

    # Matches name of QAbstractSocket.isOpen()
    def isOpen(self):
        if self.connection:
            return self.connection.isOpen()
        return False

    # Qt signal/slot based reading of websocket, or from TCP socket after assembling header and body.
    def _processBinaryMessage(self, bytes):
        if isinstance(bytes, bytearray):
            hdr = Messaging.hdr(bytes)
        else:
            # Assume this is a QByteArray from a websocket
            hdr = Messaging.hdr(bytes.data())

        # if we got this far, we have a whole message!
        # Emit the signal as a header.
        self.rx_hdr.emit(hdr)
        # If anyone is connected to the rx_msg signal then construct a message object
        # and emit that, too.
        if self.receivers(self.rx_msg):
            msg = Messaging.MsgFactory(hdr)
            self.rx_msg.emit(msg)

    # Qt signal/slot based reading of TCP socket
    def _readRxBuffer(self):
        input_stream = QtCore.QDataStream(self.connection)
        while(self.connection.bytesAvailable() > 0):
            # read the header, unless we have the header
            if(len(self.rx_buf) < Messaging.hdrSize):
                #print("reading", Messaging.hdrSize - len(self.rx_buf), "bytes for header")
                self.rx_buf += input_stream.readRawData(Messaging.hdrSize - len(self.rx_buf))
                #print("have", len(self.rx_buf), "bytes")
            
            # if we still don't have the header, break
            if(len(self.rx_buf) < Messaging.hdrSize):
                print("don't have full header, quitting")
                return
            
            hdr = Messaging.hdr(self.rx_buf)
            
            # need to decode body len to read the body
            bodyLen = hdr.GetDataLength()
            
            # read the body, unless we have the body
            if(len(self.rx_buf) < Messaging.hdrSize + bodyLen):
                #print("reading", Messaging.hdrSize + bodyLen - len(self.rx_buf), "bytes for body")
                self.rx_buf += input_stream.readRawData(Messaging.hdrSize + bodyLen - len(self.rx_buf))
            
            # if we still don't have the body, break
            if(len(self.rx_buf) < Messaging.hdrSize + bodyLen):
                print("don't have full body, quitting")
                return

            # Process what we assume to be a full message...            
            self._processBinaryMessage(self.rx_buf)

            # then clear the buffer, so we start over on the next message
            self.rx_buf = bytearray()
