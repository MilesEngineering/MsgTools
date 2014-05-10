import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *

class MsgGui(QtGui.QMainWindow):
    def __init__(self, msgdir, name, argv, parent=None):
        QtGui.QMainWindow.__init__(self,parent)
        self.name = name
        if(len(sys.argv) > 1):
            connectionType = sys.argv[1]
        else:
            connectionType = "qtsocket"
        if(len(sys.argv) > 2):
            connectionName = sys.argv[2]
        else:
            connectionName = "127.0.0.1:5678"

        label = QLabel("<font size=40>Some Text</font>")
        self.setCentralWidget(label)
         
        self.resize(320, 240)
        self.setWindowTitle(self.name)
        #self.show()  # runs the event loop?

        #sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "../../Messaging/obj/Python")
        import Messaging
        import MsgApp
        self.msgLib = Messaging.Messaging(msgdir, None, self)
        self.msgApp = MsgApp.MsgApp()

        self.msgApp.OpenConnection(connectionType, connectionName)

        # event-based way of getting messages
        # ought to connect to my own pure-virtual slot, which subclasses
        # are forced to override
        #self.msgLib.RxMsg.connect(ProcessMessage)
