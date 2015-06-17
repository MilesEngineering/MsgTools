import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

sys.path.append("../MsgApp")
from MsgApp import *

from MessageServer import *

class MsgServerGUI(QMainWindow):
    def __init__(self, msgdir, argv):
        QtGui.QMainWindow.__init__(self)

        self.server = MessageServer()
        
        self.server.connectionfailure.connect(self.onServerConnectionFailure)
        self.server.newconnectionaccepted.connect(self.onServerNewConnectionAccepted)

        self.initializeGui()
        self.server.start()

        #sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "../../Messaging/obj/Python")
        import Messaging

    def initializeGui(self):

        # Components
        self.connectionsTable = QTableView()

        # Layout
        grid = QGridLayout()
        grid.addWidget(self.connectionsTable, 0, 0)

        # Central Widget (QMainWindow limitation)
        centralWidget = QWidget()
        centralWidget.setLayout(grid)
        self.setCentralWidget(centralWidget)

        # Main Window Stuff
        self.setWindowTitle("MessageServer 0.1")
        self.setGeometry(300, 100, 800, 400)
        self.statusBar()

    def onServerConnectionFailure(self):
        self.statusBar().showMessage("Connection Failures...")

    def onServerNewConnectionAccepted(self):
        print("New Connection!")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    server = MsgServerGUI("../../../CodeGenerator/obj/Python/", sys.argv)
    server.show()

    sys.exit(app.exec_())
