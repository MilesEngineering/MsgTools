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
        
        apps = self.programs_to_launch()
        w = QtWidgets.QWidget(self)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(0,0,0,0)
        col = 0
        row = 0
        for app_info in apps:
            app_launcher = QtWidgets.QToolButton()
            app_launcher.setText(app_info.icon_text)

            # set up icon
            icon_filename = app_info.icon_filename
            pixmap = QtGui.QPixmap(icon_filename)
            icon = QtGui.QIcon(pixmap)
            app_launcher.setIcon(icon)
            app_launcher.setIconSize(pixmap.rect().size()/2)
            app_launcher.setFixedSize(pixmap.rect().size())
            app_launcher.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

            # set up launching when clicked
            app_launcher.program_name = app_info.program_name
            app_launcher.clicked.connect(self.launch)
            
            # add to layout
            grid.addWidget(app_launcher, row, col)
            
            # adjust column and row for next icon
            col += 1
            if col >= 3:
                col = 0
                row += 1
                
        w.setLayout(grid)
        self.setCentralWidget(w)
        self.adjustSize()
        self.setFixedSize(self.size())
    
    def programs_to_launch(self):
        progs = []
        for entry_point in pkg_resources.iter_entry_points("msgtools.launcher.plugin"):
            launcher_info_fn = entry_point.load()
            launcher_info = launcher_info_fn()
            progs.append(launcher_info)
        return progs

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
