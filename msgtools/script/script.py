import sys, os

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import multiprocessing


try:
    from msgtools.script import debugger
except ImportError:
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../../..")
    sys.path.append(srcroot)
    from msgtools.script import debugger

NEW_FILE = '''\
from msgtools.lib.messaging import Messaging as M
from msgtools.lib.message import Message as Msg
from msgtools.console.client import Client

M.LoadAllMessages()
cxn = Client('example')
'''

class SimplePythonEditor(QsciScintilla):
    DEBUG_MARKER_NUM = 8

    def __init__(self, parent=None):
        super(SimplePythonEditor, self).__init__(parent)
        
        # Set the default font
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QtGui.QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QtGui.QColor("#cccccc"))

        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        self.marginClicked.connect(self.on_margin_clicked)
        self.markerDefine(QsciScintilla.Circle, self.DEBUG_MARKER_NUM)
        self.setMarkerBackgroundColor(QtGui.QColor("#1111ee"), self.DEBUG_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#ffe4e4"))

        # Set Python lexer
        # Set style for Python comments (style number 1) to a fixed-width
        # courier.
        #

        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)

        text = bytearray(str.encode("Arial"))
# 32, "Courier New"         
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, text)

        # not too small
        self.setMinimumSize(600, 450)

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.DEBUG_MARKER_NUM)
        else:
            self.markerAdd(nline, self.DEBUG_MARKER_NUM)

class MsgScript(QtWidgets.QMainWindow):
    TextOutput = QtCore.pyqtSignal(object)
    def __init__(self, parent=None):
        super(MsgScript, self).__init__(parent)
        
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
        runAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-start"), "&Run", self)
        stopAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-stop"), "&Stop", self)
        clearAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-clear"), "&Clear", self)

        debug_menu = menubar.addMenu('&Debug')
        debug_menu.addAction(runAction)
        debug_menu.addAction(pauseAction)
        debug_menu.addAction(stopAction)
        debug_menu.addAction(clearAction)
        runAction.triggered.connect(self.run_action)
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
        debug_toolbar.addAction(pauseAction)
        debug_toolbar.addAction(stopAction)
        debug_toolbar.addAction(clearAction)        
        
        self.setWindowTitle("MsgScript")

        # editor/debug window
        self.editor = SimplePythonEditor()
        self.editor.modificationChanged.connect(self.document_was_modified)
        self.editor.setText("")
        self.current_filename = ""
        last_filename = self.settings.value("last_filename", '')
        if last_filename:
            self.load_file(last_filename)
            
        # script output window
        self.scriptOutput = QtWidgets.QPlainTextEdit(self)
        self.TextOutput.connect(self.output_text)
        # capture stdout, stderr
        sys.stdout = self
        sys.stderr = self
        
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.scriptOutput)
        self.setCentralWidget(self.splitter)
        self.splitter.restoreState(self.settings.value("SplitterSize", self.splitter.saveState()));
        
        # Initialize the debug and application queues for passing messages
        self.debugq = multiprocessing.Queue()
        self.applicationq = multiprocessing.Queue()
        
        timer = QtCore.QTimer(self)
        timer.setSingleShot(False)
        timer.timeout.connect(self.poll_output)
        timer.start(100)

    # poll output from the applicationq, which is another Process
    def poll_output(self):
        while not self.applicationq.empty():
            appinfo = self.applicationq.get()
            if 'exception' in appinfo:
                self.write(str(appinfo['exception']))
            elif 'stdout' in appinfo:
                self.write(str(appinfo['stdout']))
            elif 'stderr' in appinfo:
                self.write(str(appinfo['stderr']))

    # stdout/stderr
    def write(self, data):
        self.TextOutput.emit(str(data))
    def flush(self):
        pass

    def output_text(self, message):
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
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            self.settings.setValue("last_filename", self.current_filename)
            self.settings.setValue("SplitterSize", self.splitter.saveState());
            ev.accept()
        else:
            ev.ignore()
    
    def run_action(self):
        # save the file
        self.save_file(self.current_filename)
        # Create the debug process
        self.debugprocess = multiprocessing.Process(target=debugger.debug, args=(self.applicationq, self.debugq, self.current_filename))
        self.debugprocess.start()
    
    def pause_action(self):
        pass
    
    def stop_action(self):
        pass
    
    def clear_action(self):
        self.scriptOutput.clear()

def main():
    # quiet icon warnings
    os.environ["QT_LOGGING_RULES"] = "qt.svg.warning=false"
    app = QtWidgets.QApplication(sys.argv)
    msgApp = MsgScript()
    msgApp.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
