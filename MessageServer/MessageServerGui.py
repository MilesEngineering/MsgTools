import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

sys.path.append("../MsgApp")
from MsgApp import *

from MessageServer import *
from ConnectionsTableModel import *

class MessageServerGUI(QMainWindow):
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
        self.connectionsModel = ConnectionsTableModel(self.server.connections)
        self.connectionsTable = QTableView()
        self.connectionsTable.setModel(self.connectionsModel)

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
        # Just let the AbstractTableModel know data has changed so that the table view will re-render
        self.connectionsModel.refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    server = MessageServerGUI("../../../CodeGenerator/obj/Python/", sys.argv)
    server.show()

    sys.exit(app.exec_())
