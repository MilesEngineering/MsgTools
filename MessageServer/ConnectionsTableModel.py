import sys
import uuid

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *

class ConnectionsTableModel(QAbstractTableModel):

    def __init__(self, connections):
        QAbstractTableModel.__init__(self)
        self.connectionsList = connections
        self.header = ["Host IP"]

    # Read methods

    def rowCount(self, parent):
        return len(list(self.connectionsList.values()))

    def columnCount(self, parent):
        return len(self.header)

    def data(self, index, role = Qt.DisplayRole):

        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None

        return list(self.connectionsList.values())[index.row()].name

    def headerData(self, col, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.connectionsList = sorted(self.connectionsList, key = operator.itemgetter(col))

        if order == Qt.DescendingOrder:
            self.connectionsList.reverse()
        
        self.emit(SIGNAL("layoutChanged()"))

    def refresh(self):
        self.beginInsertRows(QModelIndex(), len(self.connectionsList), len(self.connectionsList))
        self.endInsertRows()

        self.beginRemoveRows(QModelIndex(), len(self.connectionsList), len(self.connectionsList))
        self.endRemoveRows()

        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(len(self.connectionsList) - 1, 0))
