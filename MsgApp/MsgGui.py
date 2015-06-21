import sys

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

from MsgApp import *

class MsgGui(MsgApp, QMainWindow):
    def __init__(self, msgdir, name, argv, parent=None):
        QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, msgdir, name, argv)

        label = QLabel("<font size=40></font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)

        import Messaging
