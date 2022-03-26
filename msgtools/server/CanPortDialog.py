import os
from PyQt5 import QtCore, QtWidgets
from .socketcan_commands import SocketcanCommands

class SelectCanPortDialog(QtWidgets.QDialog):
    statusUpdate = QtCore.pyqtSignal(str)
    portChanged = QtCore.pyqtSignal(str,str)
    @staticmethod
    def naIfEmpty(value):
        if not value:
            return "N/A"
        return value

    def __init__(self, parent=None):
        super(SelectCanPortDialog, self).__init__(parent)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle("Select a Port")
        
        self.resize(500, 400)

        self.portsList = QtWidgets.QTreeWidget()
        openButton = QtWidgets.QPushButton("Open")
        openButton.clicked.connect(self.openPort)

        createButton = QtWidgets.QPushButton("Create")
        createButton.clicked.connect(self.createPort)

        deleteButton = QtWidgets.QPushButton("Delete")
        deleteButton.clicked.connect(self.deletePort)
        
        self._arbBitrateEdit = QtWidgets.QLineEdit("1,000,000")
        self._dataBitrateEdit = QtWidgets.QLineEdit("5,000,000")
        configureButton = QtWidgets.QPushButton("Configure")
        configureButton.clicked.connect(self.configurePort)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.portsList)
        layout.addWidget(createButton)
        layout.addWidget(openButton)
        layout.addWidget(deleteButton)
        
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(QtWidgets.QLabel("Arbitration Bitrate"))
        hLayout.addWidget(self._arbBitrateEdit)
        hLayout.addWidget(QtWidgets.QLabel("Data Bitrate"))
        hLayout.addWidget(self._dataBitrateEdit)
        hLayout.addWidget(configureButton)
        layout.addLayout(hLayout)

        self.setLayout(layout)
        
        self._socketcan = SocketcanCommands(self)
        self._socketcan.statusUpdate.connect(self.statusUpdate)
        self._socketcan.portsChanged.connect(self.setup_list)
        
        self.setup_list()
    
    # This is annoying, but we have to tell the SocketcanCommands object to stop,
    # otherwise it gets deleted with it's QProcess still running.
    def closeEvent(self, event):
        self._socketcan.stop()

    def setup_list(self):
        self.portsList.clear()
        
        buses = self._socketcan.list()
        
        if len(buses) > 0:
            tableHeader = list(buses[0].keys())
            self.portsList.setHeaderLabels(tableHeader)
            for info in buses:
                tableElems = [str(x) for x in info.values()]
                self.portsList.addTopLevelItem(QtWidgets.QTreeWidgetItem(None, tableElems))
        else:
            tableHeader = ["interface", "channel"]
            self.portsList.setHeaderLabels(tableHeader)
        create_item = QtWidgets.QTreeWidgetItem(None, ["new vcan", "[NAME]"])
        create_item.setFlags(create_item.flags() | QtCore.Qt.ItemIsEditable)

        self.portsList.addTopLevelItem(create_item)

        for i in range(0, len(tableHeader)):
            self.portsList.resizeColumnToContents(i)
    
    def createPort(self):
        cur_item = self.portsList.currentItem()
        self._socketcan.create(cur_item.text(1))

    def deletePort(self):
        cur_item = self.portsList.currentItem()
        self._socketcan.delete(cur_item.text(1))

    def configurePort(self):
        cur_item = self.portsList.currentItem()
        arb_bitrate = int(self._arbBitrateEdit.text().replace(",",""))
        data_bitrate = int(self._dataBitrateEdit.text().replace(",",""))
        self._socketcan.configure(cur_item.text(1), arb_bitrate, data_bitrate)

    def openPort(self):
        cur_item = self.portsList.currentItem()
        if cur_item is not None:
            interface = cur_item.text(0)
            channel = cur_item.text(1)
            self.portChanged.emit(interface, channel)
            self.close()

