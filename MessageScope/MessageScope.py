#!/cygdrive/c/Python34/python.exe
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *
from PySide.QtCore import Qt

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append("../MsgApp")
import MsgGui

class MessageScope(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        #MsgGui.MsgGui.__init__(self, "../../../CodeGenerator/obj/Python/", "Message Scope 0.1", argv, parent)
        MsgGui.MsgGui.__init__(self, "../CodeGenerator/obj/Python/", "Message Scope 0.1", argv, parent)

        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        hSplitter = QSplitter(parent);
        
        txSplitter = QSplitter(parent);
        rxSplitter = QSplitter(parent);
        txSplitter.setOrientation(Qt.Vertical)
        rxSplitter.setOrientation(Qt.Vertical)
        hSplitter.addWidget(txSplitter)
        hSplitter.addWidget(rxSplitter)
        
        self.txDictionary = QListWidget(parent);
        self.rxDictionary = QListWidget(parent);
        self.txMsgs = QTreeWidget(parent);
        self.rxMsgs = QTreeWidget(parent);
        txSplitter.addWidget(self.txDictionary);
        txSplitter.addWidget(self.txMsgs);
        rxSplitter.addWidget(self.rxDictionary);
        rxSplitter.addWidget(self.rxMsgs);

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QTabWidget(self)
        self.setCentralWidget(hSplitter)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
        
        self.resize(800, 600)
        
        self.ReadTxDictionary()


    def ReadTxDictionary(self):
        print("Tx Dictionary:")
        for id in self.msgLib.MsgNameFromID:
            print(self.msgLib.MsgNameFromID[id], "=", id)
            newItem = QListWidgetItem()
            newItem.setText(self.msgLib.MsgNameFromID[id])
            self.txDictionary.addItem(newItem)

    def ProcessMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        id       = self.msgLib.GetID(msg)
        msgClass = self.msgLib.MsgNameFromID[id]
        methods  = self.msgLib.ListMsgGetters(msgClass)

        if(msgClass == None):
            print("WARNING!  No definition for ", id, "!\n")
            return

        if(not(id in self.msgWidgets)):
            # create a new tree widget
            msgWidget = QtGui.QTreeWidget()
            
            # add it to the tab widget, so the user can see it
            self.tabWidget.addTab(msgWidget, msgClass.__name__)
            
            # add headers, one for each message field
            header = QtCore.QStringList()
            for method in methods:
                # skip over the first three letters (which are always "Get")
                name = method.__name__.replace("Get", "", 1)
                header.append(name)
            
            msgWidget.setHeaderLabels(header)
            count = 0
            for method in methods:
                msgWidget.resizeColumnToContents(count)
                count += 1
            
            # store a pointer to it, so we can find it next time (instead of creating it again)
            self.msgWidgets[id] = msgWidget
        
        #methods = self.msgLib.ListMsgGetters(self.msgLib.headerClass)
        #for method in methods:
        #    print "hdr.", self.msgLib.headerClass.__name__, ".", method.__name__, "=", method(msg), " #", method.__doc__
        #print ""
        
        msgStringList = QtCore.QStringList()
        for method in methods:
            if(method.count == 1):
                columnText = str(method(msg))
                #print("body.",msgClass.__name__, ".", , " = ", method(msg), " #", method.__doc__, "in", method.units)
            else:
                columnText = ""
                for i in range(0,method.count):
                    #print("body.",msgClass.__name__, ".", method.__name__, "[",i,"] = ", method(msg,i), " #", method.__doc__, "in", method.units)
                    columnText += ", " + str(method(msg,i))
            msgStringList.append(columnText)
        msgItem = QTreeWidgetItem(None,msgStringList)
        self.msgWidgets[id].addTopLevelItem(msgItem)

# main starts here
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    msgApp = MessageScope(sys.argv)
    msgApp.show()
    sys.exit(app.exec_())
