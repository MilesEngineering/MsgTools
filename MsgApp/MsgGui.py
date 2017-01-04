import sys

from PyQt5 import QtGui, QtWidgets, QtCore, QtNetwork

from MsgApp import *

class MsgGui(MsgApp, QtWidgets.QMainWindow):
    def __init__(self, name, argv, options, parent=None):
        # default to Network, unless we have a input filename that contains .txt
        headerName = "BMAPHeader"
        if any(".txt" in s for s in argv) or any(".TXT" in s for s in argv):
            headerName = "SerialHeader"

        QtWidgets.QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, name, headerName, argv, options)

        label = QtWidgets.QLabel("<font size=40></font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)

        import Messaging
