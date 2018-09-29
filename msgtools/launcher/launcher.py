#!/usr/bin/env python3
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import pkg_resources

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
        
        apps = ['server', 'scope', 'inspector', 'debug', 'noisemaker']
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
                app_launcher = QtWidgets.QToolButton()
                app_launcher.setText(apps[app_index])

                # set up icon
                icon_access = "%s/%s.png" % (apps[app_index], apps[app_index])
                icon_filename = pkg_resources.resource_filename('msgtools', icon_access)
                pixmap = QtGui.QPixmap(icon_filename)
                icon = QtGui.QIcon(pixmap)
                app_launcher.setIcon(icon)
                app_launcher.setIconSize(pixmap.rect().size()/2)
                app_launcher.setFixedSize(pixmap.rect().size())
                app_launcher.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

                # set up launching when clicked
                app_launcher.program_name = 'msg' + apps[app_index]
                app_launcher.clicked.connect(self.launch)
                
                # add to layout
                grid.addWidget(app_launcher, row, col)
                app_index += 1
            row += 1
                
        w.setLayout(grid)
        self.setCentralWidget(w)
        self.adjustSize()
        self.setFixedSize(self.size())

    def launch(self):
        sender = self.sender()
        if self.connectionName and sender.program_name != "msgserver":
            args = ['--connectionName='+self.connectionName]
        else:
            args = []
        QtCore.QProcess.startDetached(sender.program_name, args)

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
