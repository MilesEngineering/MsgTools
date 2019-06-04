import os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtSerialPort import QSerialPortInfo

class SelectSerialportDialog(QtWidgets.QDialog):
    portChanged = QtCore.pyqtSignal(str)
    @staticmethod
    def naIfEmpty(value):
        if not value:
            return "N/A"
        return value
    @staticmethod
    def naIfEmptyHex(value):
        if not value:
            return "N/A"
        try:
            return hex(int(value))
        except ValueError:
            pass
        return value
    def serialPortAlias(self, info):
        for name in os.listdir("/dev/"):
            if name not in (os.curdir, os.pardir):
                full = os.path.join("/dev", name)
                if os.path.islink(full):
                    if info.portName() == os.readlink(full):
                        return full.replace("/dev/","")
        return info.portName()

    def __init__(self, parent=None):
        super(SelectSerialportDialog, self).__init__(parent)
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

        tableHeader = ["Name", "Description", "Mfg", "Serial#", "Location", "VendorID", "ProductID"]
        self.portsList.setHeaderLabels(tableHeader)
        for info in QSerialPortInfo.availablePorts():
            list = []
            description = info.description()
            manufacturer = info.manufacturer()
            serialNumber = info.serialNumber()
            list.append(self.serialPortAlias(info))
            list.append(self.naIfEmpty(description))
            list.append(self.naIfEmpty(manufacturer))
            list.append(self.naIfEmpty(serialNumber))
            list.append(info.systemLocation())
            list.append(self.naIfEmptyHex(info.vendorIdentifier()))
            list.append(self.naIfEmptyHex(info.productIdentifier()))

            self.portsList.addTopLevelItem(QtWidgets.QTreeWidgetItem(None, list))
        for i in range(0, len(tableHeader)):
            self.portsList.resizeColumnToContents(i)
        
    def openPort(self):
        cur_item = self.portsList.currentItem()
        if cur_item is not None:
            name = cur_item.text(0)
            print('opening %s' % name)
            self.portChanged.emit(name)
            self.close()

