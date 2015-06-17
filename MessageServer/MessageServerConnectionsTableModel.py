import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

class MessageServerConnectionsTableModel(QAbstractTableModel):

    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.connectionsList = []
        self.header = ["Host IP"]

    # Read methods

    def rowCount(self, parent):
        return len(self.connectionsList)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None

        return self.connectionsList[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.connectionsList = sorted(self.connectionsList,
            key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.connectionsList.reverse()
        self.emit(SIGNAL("layoutChanged()"))

    # Write Methods

    def setData(self, index, value):
        self.dataChanged(index.row(), index.column())
