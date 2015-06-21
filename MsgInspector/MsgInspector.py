#!/cygdrive/c/Python27/python.exe
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append("../MsgApp")
import MsgGui

class MsgInspector(MsgGui.MsgGui):
    def __init__(self, argv, parent=None):
        MsgGui.MsgGui.__init__(self, "../../../CodeGenerator/obj/Python/", "Message Inspector 0.1", argv, parent)
        
        self.outputType = "gui"
        self.outputName = "log.csv"
        if(len(argv) > 3):
            self.outputType = argv[3]
        if(len(argv) > 4):
            self.outputName = argv[4]
        else:
            if(self.connectionType.lower() == "file"):
                self.outputName = self.connectionName + ".csv"

        if(self.outputType.lower() == "file"):
            # event-based way of getting messages
            self.RxMsg.connect(self.PrintMessage)
            
            # hash table to lookup the widget for a message, by message ID
            self.msgWidgets = {}
        else:
            # event-based way of getting messages
            self.RxMsg.connect(self.ShowMessage)

            # tab widget to show multiple messages, one per tab
            self.tabWidget = QTabWidget(self)
            self.setCentralWidget(self.tabWidget)
            self.resize(640, 480)
        
            # hash table to lookup the widget for a message, by message ID
            self.msgWidgets = {}


    def ShowMessage(self, msg):
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

    def PrintMessage(self, msg):
        # read the ID, and get the message name, so we can print stuff about the body
        id       = self.msgLib.GetID(msg)
        msgClass = self.msgLib.MsgNameFromID[id]
        methods  = self.msgLib.ListMsgGetters(msgClass)

        if(msgClass == None):
            print("WARNING!  No definition for ", id, "!\n")
            return

        # if we write CSV to multiple files, we'd probably look up a hash table for this message id,
        # and open it and write a header
        if(0):
            if(not(id in self.outputFiles)):
                # create a new file
                outputFile = "open a file for writing, with filename based on self.outputName and messagename"
                
                # add headers, one for each message field
                header = ""
                for method in methods:
                    # skip over the first three letters (which are always "Get")
                    name = method.__name__.replace("Get", "", 1)
                    header += name + ", "
                
                print(header)
                # store a pointer to it, so we can find it next time (instead of creating it again)
                self.outputFiles[id] = outputFile
        
        #methods = self.msgLib.ListMsgGetters(self.msgLib.headerClass)
        #for method in methods:
        #    print "hdr.", self.msgLib.headerClass.__name__, ".", method.__name__, "=", method(msg), " #", method.__doc__
        #print ""
        
        text = ""
        for method in methods:
            if(method.count == 1):
                columnText = str(method(msg))
                #print("body.",msgClass.__name__, ".", , " = ", method(msg), " #", method.__doc__, "in", method.units)
            else:
                columnText = ""
                for i in range(0,method.count):
                    #print("body.",msgClass.__name__, ".", method.__name__, "[",i,"] = ", method(msg,i), " #", method.__doc__, "in", method.units)
                    columnText += ", " + str(method(msg,i))
            text += columnText + ", "
        print(text)

# main starts here
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    msgApp = MsgInspector(sys.argv)
    #msgApp.msgLib.PrintDictionary()
    msgApp.show()
    sys.exit(app.exec_())
