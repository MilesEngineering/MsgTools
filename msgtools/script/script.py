import sys, os, multiprocessing
from PyQt5 import QtWidgets, QtCore, QtGui

from msgtools.script.edit_window import EditWindow
from msgtools.script import debugger as debugger
import msgtools.script.launcher as launcher

NEW_FILE = '''\
from msgtools.lib.messaging import Messaging as M
from msgtools.lib.message import Message as Msg
from msgtools.console.client import Client

M.LoadAllMessages()
cxn = Client('example')
'''

class MsgScript(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MsgScript, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon(launcher.info().icon_filename))
        
        self.settings = QtCore.QSettings("MsgTools", 'MsgScript')
        self.restoreGeometry(self.settings.value("geometry", QtCore.QByteArray()))
        self.restoreState(self.settings.value("windowState", QtCore.QByteArray()))
        
        # status bar
        self.statusBar().showMessage("")
                
        # menu bar
        newAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-new"), '&New', self)
        openAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-open"), '&Open', self)
        closeAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-close"), '&Close', self)
        saveAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save', self)
        saveAsAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("document-save-as"), 'Save &As', self)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(newAction)
        file_menu.addAction(openAction)
        file_menu.addAction(closeAction)
        file_menu.addAction(saveAction)
        file_menu.addAction(saveAsAction)
        newAction.triggered.connect(self.new_action)
        openAction.triggered.connect(self.open_action)
        closeAction.triggered.connect(self.close_action)
        saveAction.triggered.connect(self.save_action)
        saveAsAction.triggered.connect(self.save_as_action)

        pauseAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-pause"), "&Pause", self)
        stepAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-skip-forward"), "Step &Into", self)
        stepOutAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-seek-forward"), "Step &Oout", self)
        runAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-start"), "&Run", self)
        stopAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-stop"), "&Stop", self)
        clearAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("user-trash"), "&Clear", self)
        stepTimeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        stepTimeSlider.setMinimum(0)
        stepTimeSlider.setMaximum(3)
        stepTimeSlider.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        debug_menu = menubar.addMenu('&Debug')
        debug_menu.addAction(runAction)
        debug_menu.addAction(pauseAction)
        debug_menu.addAction(stopAction)
        debug_menu.addAction(clearAction)
        runAction.triggered.connect(self.run_action)
        stepAction.triggered.connect(self.step_action)
        stepOutAction.triggered.connect(self.step_out_action)
        pauseAction.triggered.connect(self.pause_action)
        stopAction.triggered.connect(self.stop_action)
        clearAction.triggered.connect(self.clear_action)
        
        # toolbars
        file_toolbar = self.addToolBar("File")
        file_toolbar.setObjectName("file_toolbar")
        file_toolbar.addAction(newAction)
        file_toolbar.addAction(openAction)
        file_toolbar.addAction(closeAction)
        file_toolbar.addAction(saveAction)
        file_toolbar.addAction(saveAsAction)
        
        debug_toolbar = self.addToolBar("Debug")
        debug_toolbar.setObjectName("debug_toolbar")
        debug_toolbar.addAction(runAction)
        debug_toolbar.addAction(stepAction)
        debug_toolbar.addAction(stepOutAction)
        debug_toolbar.addAction(pauseAction)
        debug_toolbar.addAction(stopAction)
        debug_toolbar.addAction(clearAction)
        debug_toolbar.addWidget(QtWidgets.QLabel("Step Time"))
        debug_toolbar.addWidget(stepTimeSlider)
        
        self.setWindowTitle("MsgScript")

        # editor/debug window
        self.editor = EditWindow()
        self.editor.modificationChanged.connect(self.document_was_modified)
        self.editor.setText("")
        self.current_filename = ""
        last_filename = self.settings.value("last_filename", '')
        if last_filename:
            self.load_file(last_filename)
            
        # script output window
        self.scriptOutput = QtWidgets.QPlainTextEdit(self)
        
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.scriptOutput)
        self.setCentralWidget(self.splitter)
        self.splitter.restoreState(self.settings.value("SplitterSize", self.splitter.saveState()));
        
        # Initialize the debug and application queues for passing messages
        self.debugq = multiprocessing.Queue()
        self.applicationq = multiprocessing.Queue()
        
        self.debugprocess = None
        self.isrunning = False
        
        self.debug_timer = QtCore.QTimer(self)
        self.debug_timer.setSingleShot(False)
        self.debug_timer.timeout.connect(self.poll_output)
        # this determines how quickly we notice the debugger did something,
        # and in turn limits the rate of 'isrunning' auto-stepping
        stepTimeSlider.setValue(int(self.settings.value("step_time", 1)))
        self.time_slider_changed(stepTimeSlider.value())
        stepTimeSlider.valueChanged.connect(self.time_slider_changed)

    # poll output from the applicationq, which is another Process
    def poll_output(self):
        while not self.applicationq.empty():
            appinfo = self.applicationq.get()
            if 'exception' in appinfo:
                self.write("Exception: " + str(appinfo['exception']))
            elif 'stdout' in appinfo:
                self.write(str(appinfo['stdout']))
            elif 'stderr' in appinfo:
                self.write(str(appinfo['stderr']))
            elif 'error' in appinfo:
                self.editor.crashed()
            elif 'exit' in appinfo:
                self.stop_action()
            elif 'trace' in appinfo:
                tr = appinfo['trace']
                co = appinfo['co']
                #self.write("%s: line %d\n" % (co['file'], co['lineno']))
                if co['file'] == self.current_filename:
                    if self.debugprocess and self.debugprocess.is_alive():
                        self.editor.ran_to_line(co['lineno'])
                        if self.isrunning:
                            if not self.editor.has_breakpoint(co['lineno']):
                                self.debugq.put('step')
                else:
                    #open another file, switch to it's tab, show the line we're at!?!?
                    pass

    def write(self, message):
        self.scriptOutput.moveCursor(QtGui.QTextCursor.End)
        self.scriptOutput.insertPlainText(message)
        self.scriptOutput.moveCursor(QtGui.QTextCursor.End)

    def new_action(self):
        if self.maybe_save():
            self.set_current_file('')
            self.editor.setText(NEW_FILE)
            self.editor.setModified(False)
            self.set_window_modified()
    
    def open_action(self):
        if self.maybe_save():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(self)
            if filename:
                self.load_file(filename)
    
    def save_action(self):
        if self.current_filename == '':
            return self.save_as_action()
        else:
            return self.save_file(self.current_filename)
    
    def save_as_action(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.AcceptSave
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,"QtWidgets.QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if not filename:
            return False
        return self.save_file(filename)
    
    def save_file(self, filename):
        try:
            file = open(filename, 'w')
        except IOError:
            QtWidgets.QMessageBox.warning(self, "Application", "Cannot write file %1" % (filename))
            return
        else:
            with file:
                file.write(self.editor.text())
                self.set_current_file(filename)
                self.statusBar().showMessage("File saved", 2000)
        return True
    
    def load_file(self, filename):
        try:
            file = open(filename, 'r')
        except (IOError, FileNotFoundError):
            QtWidgets.QMessageBox.warning(self, "Application", "Cannot read file %s" % (filename))
            return
        else:
            with file:
                self.set_current_file(filename)
                self.editor.setText(file.read())
                self.editor.setModified(False)
                self.set_window_modified()

    def set_current_file(self, filename):
        self.editor.setModified(False)
        self.current_filename = filename
        self.set_window_modified()

    def set_window_modified(self):
        title = "MsgScript - %s" % self.current_filename
        if self.editor.isModified():
            title = title + " *"
        self.setWindowTitle(title)
    
    def document_was_modified(self, modified):
        if modified:
            self.set_window_modified()
        
    def maybe_save(self):
        if not self.editor.isModified():
            return True
        ret = QtWidgets.QMessageBox.warning(self, "Application",
                                   "The document has been modified.\nDo you want to save your changes?",
                                   QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel);
        if ret == QtWidgets.QMessageBox.Save:
            return self.save_file(self.current_filename)
        elif ret == QtWidgets.QMessageBox.Cancel:
            return False

        return True

    def close_action(self):
        self.maybe_save()
        self.set_current_file('')
        self.editor.setText('')
        self.editor.setModified(False)
        self.set_window_modified()
    
    def closeEvent(self, ev):
        if self.maybe_save():
            self.stop_action()
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            self.settings.setValue("last_filename", self.current_filename)
            self.settings.setValue("SplitterSize", self.splitter.saveState())
            ev.accept()
        else:
            ev.ignore()
    
    #We want to update the display as the script runs.  Therefore, we should never do "self.debugq.put('over')"
    #We should always step through the code, but we should track if we're "running", and if so, have reading a trace cause another 'step'
    def run_action(self):
        if self.debugprocess != None:
            if self.debugprocess.is_alive():
                #self.debugq.put('over')
                self.isrunning = True
                if self.debugq.empty():
                    self.debugq.put('step')
            else:
                self.debugprocess = None
        if self.debugprocess == None:
            # save the file
            self.save_file(self.current_filename)
            # clear the queues, in case there was anything left over from last run
            self.debugq = multiprocessing.Queue()
            self.applicationq = multiprocessing.Queue()
            # Create the debug process
            self.debugprocess = multiprocessing.Process(target=debugger.debug, args=(self.applicationq, self.debugq, self.current_filename))
            self.debugprocess.start()
            #self.debugprocess.exited.connect(self.process_ended)
    
    def step_action(self):
        if self.debugprocess:
            if self.debugq.empty():
                self.debugq.put('step')
        else:
            self.write('not running')
    
    def step_out_action(self):
        if self.debugprocess:
            if self.debugq.empty():
                self.debugq.put('over')
        else:
            self.write('not running')
    
    def pause_action(self):
        self.isrunning = False
        pass
    
    def stop_action(self):
        self.isrunning = False
        if self.debugprocess != None:
            i = 0
            while(self.debugprocess.is_alive()):
                if i > 0:
                    self.write("Tried to terminate and join(0.1), but still is_alive()!")
                i+=1
                if i > 5:
                    self.write("Couldn't kill script!")
                    return
                self.debugprocess.terminate()
                # This can hang forever!  For some reason the join may block forever, but if
                # we let it timeout is_alive() will return false and we break out of the loop!
                self.debugprocess.join(0.1)
            self.debugprocess = None
            self.editor.exited()
        else:
            self.editor.ran_to_line(0)
    
    def clear_action(self):
        self.scriptOutput.clear()
    
    def time_slider_changed(self, value):
        self.settings.setValue("step_time", value)
        time_val = 100
        if value == 0:
            time_val = 10
        elif value == 1:
            time_val = 100
        elif value == 2:
            time_val = 500
        elif value == 3:
            time_val = 1000
        self.debug_timer.start(time_val)

def main():
    # quiet icon warnings
    os.environ["QT_LOGGING_RULES"] = "qt.svg.warning=false"
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgScript()
    msgApp.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
