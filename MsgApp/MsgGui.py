import sys

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

from MsgApp import *

class MsgGui(MsgApp, QMainWindow):
    def __init__(self, name, argv, parent=None):
        # default to Network, unless we have a input filename that contains .txt
        headerName = "Network"
        if any(".txt" in s for s in argv):
            headerName = "Serial"

        QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, name, headerName, argv)

        label = QLabel("<font size=40></font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)

        import Messaging
