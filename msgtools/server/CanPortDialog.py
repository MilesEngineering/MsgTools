import os
from PyQt5 import QtCore, QtWidgets
import can

class SelectCanPortDialog(QtWidgets.QDialog):
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
        
        self.resize(800, 200)

        self.portsList = QtWidgets.QTreeWidget()
        openButton = QtWidgets.QPushButton("Open")
        openButton.clicked.connect(self.openPort)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.portsList)
        layout.addWidget(openButton)
        self.setLayout(layout)

        buses = can.detect_available_configs(['socketcan', "pcan", "virtual"])
        if len(buses) > 0:
            tableHeader = list(buses[0].keys())
            self.portsList.setHeaderLabels(tableHeader)
            for info in buses:
                tableElems = [str(x) for x in info.values()]
                self.portsList.addTopLevelItem(QtWidgets.QTreeWidgetItem(None, tableElems))
        else:
            tableHeader = ["Interfaces", "Configs"]
            self.portsList.setHeaderLabels(tableHeader)


        for i in range(0, len(tableHeader)):
            self.portsList.resizeColumnToContents(i)
        
    def openPort(self):
        cur_item = self.portsList.currentItem()
        if cur_item is not None:
            interface = cur_item.text(0)
            channel = cur_item.text(1)
            self.portChanged.emit(interface, channel)
            self.close()

