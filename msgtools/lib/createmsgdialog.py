from PyQt5 import QtCore, QtWidgets

from msgtools.lib.messaging import Messaging

class DialogFieldInfo:
    def __init__(self, fieldInfo):
        self.fieldInfo = fieldInfo
        if fieldInfo.type == "enumeration":
            self.widget = QtWidgets.QComboBox()
            self.widget.addItems(fieldInfo.enum[0].keys())
            # there's some odd behavior in the UI when the box is editable :(
            # if you want it editable, uncomment this line, and play around and see if you like it
            #self.widget.setEditable(1)
            # store a hash table of value->ComboBoxIndex
            # this is NOT the same as value->enumIndex!
            self.comboBoxIndexOfEnum = {}
            for i in range(0, self.widget.count()):
                self.comboBoxIndexOfEnum[self.widget.itemText(i)] = i
        else:
            self.widget = QtWidgets.QLineEdit()
    def setValueInMsg(self, msg):
        #TODO ought to handle arrays, bitfields, enums
        if self.fieldInfo.type == "enumeration":
            value = self.widget.currentText()
        else:
            value = self.widget.text()
        Messaging.set(msg, self.fieldInfo, value)

# dialog box to let user enter fields of a message and send it
class CreateMsgDialog(QtWidgets.QDialog):
    def __init__(self, parent, msgClass):
        super(CreateMsgDialog, self).__init__(parent)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle(msgClass.MsgName())
        
        # construct a message to store data into
        self.msg = msgClass()
        
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.headerFields = []
        for fieldInfo in Messaging.hdr.fields:
            if fieldInfo.bitfieldInfo:
                for bitfieldInfo in fieldInfo.bitfieldInfo:
                    if bitfieldInfo.idbits == 0 and bitfieldInfo.name != "DataLength" and bitfieldInfo.name != "Time":
                        field = DialogFieldInfo(bitfieldInfo)
                        self.headerFields.append(field)
                        layout.addRow(QtWidgets.QLabel(bitfieldInfo.name), field.widget)
            else:
                if fieldInfo.idbits == 0 and fieldInfo.name != "DataLength" and fieldInfo.name != "Time":
                    field = DialogFieldInfo(fieldInfo)
                    self.headerFields.append(field)
                    layout.addRow(QtWidgets.QLabel(fieldInfo.name), field.widget)
        
        self.msgFields = []
        for fieldInfo in msgClass.fields:
            field = DialogFieldInfo(fieldInfo)
            self.msgFields.append(field)
            layout.addRow(QtWidgets.QLabel(fieldInfo.name), field.widget)

        buttonBox = QtWidgets.QDialogButtonBox(self)
        #buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.constructMessage)
        buttonBox.rejected.connect(self.reject)
        layout.addRow(buttonBox)

    def constructMessage(self):
        for field in self.headerFields:
            field.setValueInMsg(self.msg.hdr)
        for field in self.msgFields:
            field.setValueInMsg(self.msg)
        self.accept()
