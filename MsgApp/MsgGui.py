import sys
from PySide import QtCore, QtGui, QtNetwork
from PySide.QtGui import *

from MsgApp import *

class MsgGui(MsgApp, QtGui.QMainWindow):
    def __init__(self, msgdir, name, argv, parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        MsgApp.__init__(self, msgdir, name, argv)

        label = QLabel("<font size=40>Some Text</font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)
        #self.show()  # runs the event loop?

        #sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "../../Messaging/obj/Python")
        import Messaging

        # event-based way of getting messages
        # ought to connect to my own pure-virtual slot, which subclasses
        # are forced to override
        #self.msgLib.RxMsg.connect(ProcessMessage)
