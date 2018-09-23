#!/usr/bin/env python3
import sys
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging
import msgtools.lib.gui

DESCRIPTION='''MsgLauncher launches msgtools applications.  It gives them relevant settings (like server
IP address and port) when it starts them.'''

class MsgLauncher(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self,parent)

        # persistent settings
        self.settings = QtCore.QSettings("MsgTools", "launcher")
        
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))

        self.connectionName = self.settings.value("connection", "")
        
        settingsAction = QtWidgets.QAction('&Settings', self)
        menubar = self.menuBar()
        connectMenu = menubar.addMenu('&Connection')
        connectMenu.addAction(settingsAction)
        settingsAction.triggered.connect(self.chooseHost)
        
        self.setWindowTitle("MsgLauncher")
        
        apps = ['msgserver', 'msgscope', 'msginspector', 'msgdebug', 'msgnoisemaker']
        w = QtWidgets.QWidget(self)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(0,0,0,0)
        app_index = 0
        row = 0
        while app_index < len(apps):
            for col in range(3):
                if app_index >= len(apps):
                    break
                app_launcher = QtWidgets.QPushButton(apps[app_index])
                app_launcher.program_name = apps[app_index]
                app_launcher.clicked.connect(self.launch)
                grid.addWidget(app_launcher, row, col)
                app_index += 1
            row += 1
                
        w.setLayout(grid)
        self.setCentralWidget(w)

    def launch(self):
        sender = self.sender()
        print("launch " + sender.program_name)
        subprocess.call(sender.program_name)

    def chooseHost(self):
        userInput, ok = QtWidgets.QInputDialog.getText(self, 'Connect',  'Server:', QtWidgets.QLineEdit.Normal, self.connectionName)
        if ok:
            self.connectionName = userInput
            self.settings.setValue("connection", self.connectionName)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("connection", self.connectionName)
        super(QtWidgets.QMainWindow, self).closeEvent(event)

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgLauncher()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
