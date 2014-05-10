#!/cygdrive/c/Python27/python.exe
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append("../MsgApp")
import MsgApp

class MsgInspector(MsgApp.MsgApp):
    def __init__(self, argv, parent=None):
        MsgApp.MsgApp.__init__(self, "../../../CodeGenerator/obj/Python/", "Message Inspector 0.1", argv, parent)
        # event-based way of getting messages
        self.RxMsg.connect(self.ProcessMessage)

        # tab widget to show multiple messages, one per tab
        self.tabWidget = QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        
        # hash table to lookup the widget for a message, by message ID
        self.msgWidgets = {}
        
        self.resize(640, 480)


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
    msgApp = MsgInspector(sys.argv)
    #msgApp.msgLib.PrintDictionary()
    msgApp.show()
    sys.exit(app.exec_())
