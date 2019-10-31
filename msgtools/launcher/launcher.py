#!/usr/bin/env python3
import sys, os
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
import pkg_resources
from . import codegen_gui

DESCRIPTION='''MsgLauncher launches msgtools applications.  It gives them relevant settings (like server
IP address and port) when it starts them.'''

class DetachableProcess(QtCore.QProcess):
    def __init__(self):
        QtCore.QProcess.__init__(self)
    def detach(self):
        self.waitForStarted()
        self.setProcessState(QtCore.QProcess.NotRunning);

    
class MsgLauncher(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self,parent)
        
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('--connectionName', default=None,
            help='''The connection name.  For socket connections this is an IP and port e.g. 127.0.0.1:5678.  
                    You may prepend ws:// to indicate you want to use a Websocket instead.  For file 
                    connection types, this is the filename to use as a message source.
                    This parameter is overridden by the --ip and --port options.''')
        parser.add_argument('--msgdir', help=''''The directory to load Python message source from.''')
        args = parser.parse_args()
        args.msgdir = None if hasattr(args, 'msgdir') == False else args.msgdir
        self.msgdir = args.msgdir

        # persistent settings
        self.settings = QtCore.QSettings("MsgTools", "launcher")
        
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))

        self.connectionName = self.settings.value("connection", "")
        
        if args.connectionName != None:
            self.connectionName = args.connectionName
        
        settingsAction = QtWidgets.QAction('&Settings', self)
        menubar = self.menuBar()
        connectMenu = menubar.addMenu('&Connection')
        connectMenu.addAction(settingsAction)
        settingsAction.triggered.connect(self.chooseHost)
        
        if os.path.exists('/opt/msgtools/messages'):
            self.codegen_gui = codegen_gui.CodegenGui(menubar, self.settings)
        
        self.setWindowTitle("MsgLauncher")
        
        # list of everything we launched
        self.procs = []
        
        # get list of programs to put into the launcher
        apps = self.programs_to_launch()
        
        # create a grid for launcher buttons
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(0,0,0,0)
        num_cols = 3
        col = 0
        row = 0
        for k in sorted(apps):
            app_info = apps[k]
            app_launcher = QtWidgets.QToolButton()
            app_launcher.setText(app_info.icon_text)

            # set up icon
            icon_filename = app_info.icon_filename
            if os.path.exists(icon_filename):
                pixmap = QtGui.QPixmap(icon_filename)
                icon = QtGui.QIcon(pixmap)
                app_launcher.setIcon(icon)
                app_launcher.setIconSize(pixmap.rect().size()/2)
                app_launcher.setFixedSize(pixmap.rect().size())
                app_launcher.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            else:
                print("ERROR!  %s does not exist!" % icon_filename)

            # set up launching when clicked
            app_launcher.program_name = app_info.program_name
            app_launcher.clicked.connect(self.launch)
            
            # add to layout
            grid.addWidget(app_launcher, row, col)
            
            # adjust column and row for next icon
            col += 1
            if col >= num_cols:
                col = 0
                row += 1
                
        w = QtWidgets.QWidget(self)
        w.setLayout(grid)
        self.setCentralWidget(w)
        self.adjustSize()
        self.setFixedSize(self.size())

    def programs_to_launch(self):
        # class to store info.  can't used collections.namedtuple because it's not mutable
        class LauncherInfo:
            def __init__(self, icon_text, program_name, icon_filename, module_name):
                self.icon_text = icon_text
                self.program_name = program_name
                self.icon_filename = icon_filename
                self.module_name = module_name

        # Make a list of programs to launch
        progs = []
        exclude_msgtools = False
        # check if we were launched from source on disk, or via an installed package entry point
        if __name__ == "__main__":
            # exclude anything from installed python packages
            exclude_msgtools = True

            # look for source near our file location on disk
            basedir = os.path.abspath(os.path.dirname(__file__)) + '/..'
            for filename in os.listdir(basedir):
                if filename == "launcher":
                    continue
                dirname = os.path.abspath(basedir + "/" + filename)
                png_name = dirname+'/'+filename+'.png'
                if os.path.exists(dirname+'/launcher.py') and os.path.exists(png_name):
                    progs.append(LauncherInfo(filename, [sys.executable, dirname+'/'+filename+'.py'], png_name, 'msgtools.'+filename+'.launcher'))

        # use pkg_resources to find programs to launch
        for entry_point in pkg_resources.iter_entry_points("msgtools.launcher.plugin"):
            launcher_info_fn = entry_point.load()
            launcher_info = launcher_info_fn()
            if exclude_msgtools and entry_point.module_name.startswith('msgtools.'):
                continue
            progs.append(LauncherInfo(*launcher_info, module_name=entry_point.module_name))

        # put the list into a hash table that has keys that can be sorted
        # alphabetically to give the order we want.
        ret = {}
        for launcher_info in progs:
            # come up with a sorted name to prioritize the core apps
            # above the non-core apps, even within the msgtools package.
            sort_name = launcher_info.icon_text
            if launcher_info.module_name.startswith('msgtools.'):
                sort_name = '@'+ sort_name
                if launcher_info.module_name.startswith('msgtools.server'):
                    sort_name = '@1'+ sort_name
                elif launcher_info.module_name.startswith('msgtools.scope'):
                    sort_name = '@2'+ sort_name
                elif launcher_info.module_name.startswith('msgtools.script'):
                    sort_name = '@3'+ sort_name
                elif (launcher_info.module_name.startswith('msgtools.debug') or
                      launcher_info.module_name.startswith('msgtools.inspector')):
                    sort_name = '@'+ sort_name
                else:
                    # any msgtools. items that *aren't* in the above if/elif, will
                    # sorted after those that are.
                    pass
            if len(launcher_info.program_name) == 2:
                launcher_info.icon_text = './' + launcher_info.icon_text
                sort_name = './' + sort_name
            ret[sort_name] = launcher_info

        return ret

    def launch(self):
        sender = self.sender()
        program_name = sender.program_name
        args = []
        is_msgserver = (program_name == 'msgserver')
        if len(program_name) == 2:
            args = [program_name[1]]
            program_name = program_name[0]
            is_msgserver = args[0].endswith('msgtools/server/server.py')
        if self.connectionName and not is_msgserver:
            args = args + ['--connectionName='+self.connectionName]
        if self.msgdir:
            args.append("--msgdir="+self.msgdir)

        proc = DetachableProcess()
        proc.finished.connect(self.process_exited)
        proc.readyReadStandardOutput.connect(self.printStdOut)
        proc.readyReadStandardError.connect(self.printStdErr)
        proc.start(program_name, args)
        self.procs.append(proc)

    def chooseHost(self):
        userInput, ok = QtWidgets.QInputDialog.getText(self, 'Connect',  'Server:', QtWidgets.QLineEdit.Normal, self.connectionName)
        if ok:
            self.connectionName = userInput
            self.settings.setValue("connection", self.connectionName)

    def process_exited(self, exitCode, exitStatus):
        p = self.sender()
        self.procs.remove(p)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("connection", self.connectionName)
        
        if len(self.procs) > 0:
            ret = QtWidgets.QMessageBox.warning(
                self,
                "MsgLauncher Exiting",
                "Close launched applications?",
                QtWidgets.QMessageBox.YesToAll | QtWidgets.QMessageBox.No);
            if ret == QtWidgets.QMessageBox.YesToAll:
                for p in self.procs:
                    p.terminate()
                    p.detach()
            elif ret == QtWidgets.QMessageBox.No:
                for p in self.procs:
                    p.detach()

        try:
            self.codegen_gui.save_settings()
        except AttributeError:
            pass

        super(QtWidgets.QMainWindow, self).closeEvent(event)
    
    def printStdOut(self):
        sender = self.sender()
        print(str(sender.readAllStandardOutput(), encoding='utf-8'))

    def printStdErr(self):
        sender = self.sender()
        print(str(sender.readAllStandardError(), encoding='utf-8'))

def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgLauncher()
    msgApp.show()
    sys.exit(app.exec_())

# main starts here
if __name__ == '__main__':
    main()
