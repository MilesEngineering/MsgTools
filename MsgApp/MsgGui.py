import sys

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork

from MsgApp import *

class MsgGui(MsgApp, QtWidgets.QMainWindow):
    def __init__(self, name, argv, options, parent=None):
        # default to Network, unless we have a input filename that contains .txt
        headerName = "NetworkHeader"
        if any(".txt" in s for s in argv) or any(".TXT" in s for s in argv):
            headerName = "SerialHeader"

        QtWidgets.QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, name, headerName, argv, options)

        # make a status bar to print status messages
        self.status = QtWidgets.QLabel("Initializing")
        self.statusBar().addPermanentWidget(self.status)
        # hook it up to our base class statusUpdate signal
        self.statusUpdate.connect(self.status.setText)
        
        self.resize(320, 240)
        self.setWindowTitle(self.name)

        # create menu items, connect them to socket operations
        if(self.connectionType.lower() == "socket" or self.connectionType.lower() == "qtsocket"):
            connectAction = QtWidgets.QAction('&Connect', self)
            disconnectAction = QtWidgets.QAction('&Disconnect', self)

            menubar = self.menuBar()
            connectMenu = menubar.addMenu('&Connect')
            connectMenu.addAction(connectAction)
            connectMenu.addAction(disconnectAction)
            connectAction.triggered.connect(self.chooseHost)
            disconnectAction.triggered.connect(self.connection. disconnectFromHost)
    
    # open dialog box to choose host to connect to
    def chooseHost(self):
        (hostIp, port) = self.connectionName.split(":")
        if(hostIp == None):
            hostIp = "127.0.0.1"

        if(port == None):
            port = "5678"
        
        port = int(port)

        hostIp, ok = QInputDialog.getText(self, 'Connect',  'Server:', QLineEdit.Normal, hostIp)
        self.connection.connectToHost(hostIp, port)
    
