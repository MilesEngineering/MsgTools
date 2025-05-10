import sys
import subprocess
import os

from PyQt5 import QtCore, QtGui, QtWidgets

def find_base_dir():
    curdir = os.path.abspath(os.path.curdir)
    while(True):
        messages_dir = os.path.abspath(os.path.join(curdir, CodegenGui.MSG_SUBDIR))
        if os.path.isdir(messages_dir):
            return curdir
        parent_dir = os.path.abspath(os.path.join(curdir, '..'))
        # if our path stops changing as we go up, we got to the top
        if curdir == parent_dir:
            raise FileNotFoundError("%s does not exist upstream from %s" % (msg_dir, os.path.abspath(os.path.curdir)))
        curdir = parent_dir
    if os.path.isdir(GLOBAL_MSGTOOLS_DIR):
        return GLOBAL_MSGTOOLS_DIR
    raise FileNotFoundError("%s does not exist" % (msg_dir))

class CodegenGui(QtCore.QObject):
    GLOBAL_MSGTOOLS_DIR = "/opt/msgtools"
    MSG_SUBDIR = "messages"
    OBJ_SUBDIR = "obj/CodeGenerator"
    languageOptions = {}
    languageOptions['C']          = ["c", "C"]
    languageOptions['C++']        = ["cpp", "Cpp"]
    languageOptions['Dart']       = ["dart", "Dart/lib"]
    languageOptions['Java']       = ["java", "Java"]
    languageOptions['Javascript'] = ["javascript", "Javascript"]
    languageOptions['Matlab']     = ["matlab", "Matlab/+Messages"]
    languageOptions['Python']     = ["python", "Python"]
    languageOptions['Html']       = ["HTML", "language.py", "Template.html", "HeaderTemplate.html"]
    "find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)HTML/bootstrap.min.css"
    def __init__(self, menubar, settings):
        QtCore.QObject.__init__(self)
        self.settings = settings
        codegenMenu = menubar.addMenu('&Generate Code')

        cleanAction = QtWidgets.QAction('&Clean', self)
        cleanAction.triggered.connect(self.codegen_clean)
        codegenMenu.addAction(cleanAction)

        buildAction = QtWidgets.QAction('&Build', self)
        buildAction.triggered.connect(self.codegen)
        codegenMenu.addAction(buildAction)
        
        submenu = codegenMenu.addMenu('Languages')
        languages = self._language_options()
        allAction = QtWidgets.QAction('All', self)
        allAction.triggered.connect(self.language_selected)
        allAction.setCheckable(True)
        submenu.addAction(allAction)
        self.languageCheckboxes = []
        self.selectedLanguages = self.settings.value("languages", "").split(',')
        # remove empty string if it's there
        try:
            self.selectedLanguages.remove('')
        except ValueError:
            pass
        for language in languages:
            lAction = QtWidgets.QAction(language, self)
            lAction.triggered.connect(self.language_selected)
            lAction.setCheckable(True)
            submenu.addAction(lAction)
            self.languageCheckboxes.append(lAction)
            if language in self.selectedLanguages:
                lAction.setChecked(True)

    def language_selected(self):
        s = self.sender()
        checked = s.isChecked()
        language_name = s.text()
        if language_name == 'All':
            for languageCheckbox in self.languageCheckboxes:
                languageCheckbox.setChecked(checked)
        else:
            if checked:
                if not language_name in self.selectedLanguages:
                    self.selectedLanguages.append(language_name)
            else:
                if not language_name in self.selectedLanguages:
                    self.selectedLanguages.remove(language_name)

    def save_settings(self):
        self.settings.setValue("languages", ','.join(self.selectedLanguages))

    def codegen(self):
        commands = []
        for languageName in self.selectedLanguages:
            languageOptions = self.languageOptions[languageName]
            languagePluginName = languageOptions[0]
            outputDir = os.path.join(CodegenGui.OBJ_SUBDIR, languageOptions[1])
            invoke = 'msgparser %s %s %s' % (CodegenGui.MSG_SUBDIR, outputDir, languagePluginName)
            commands.append(invoke)
        self._invoke(commands)

    def codegen_clean(self):
        self.clean()
        
    def clean(self):
        base_dir = find_base_dir()
        obj_dir = os.path.abspath(os.path.join(base_dir, CodegenGui.OBJ_SUBDIR))
        if obj_dir.endswith(CodegenGui.OBJ_SUBDIR):
            self._invoke(['rm -rf %s' % obj_dir])
        else:
            raise FileNotFoundError("%s is invalid (needs to end with %s" % (obj_dir, CodegenGui.OBJ_SUBDIR))

    def _language_options(self):
        return self.languageOptions.keys()

    def _invoke(self, commands):
        dlg = CodeGeneratorDialog(commands)
        code = dlg.exec_()

class CodeGeneratorDialog(QtWidgets.QDialog):
    def __init__(self, commands, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.resize(600, 400);

        vlayout = QtWidgets.QVBoxLayout()
        self.setLayout(vlayout)

        self.textBox = QtWidgets.QPlainTextEdit()
        self.textBox.setReadOnly(True)
        vlayout.addWidget(self.textBox)

        self.ok = QtWidgets.QPushButton("OK")
        self.ok.setEnabled(False)
        self.ok.clicked.connect(self.accept)
        vlayout.addWidget(self.ok)

        self.commands = commands
        self.start_process(self.commands.pop())
    
    def start_process(self, command):
        base_dir = find_base_dir()
        self.textBox.insertPlainText('> %s\n' % command)
        self.textBox.moveCursor(QtGui.QTextCursor.End)
        self.proc = QtCore.QProcess()
        self.proc.finished.connect(self.process_exited)
        self.proc.readyReadStandardOutput.connect(self.print_output)
        self.proc.readyReadStandardError.connect(self.print_output)
        self.proc.setWorkingDirectory(base_dir)
        self.proc.start(command)

    def process_exited(self):
        self.textBox.moveCursor(QtGui.QTextCursor.End)
        self.textBox.insertPlainText("\nDone!\n")
        self.textBox.moveCursor(QtGui.QTextCursor.End)
        if len(self.commands) > 0:
            self.start_process(self.commands.pop())
        else:
            #self.accept()
            self.ok.setEnabled(True)

    def print_output(self):
        QtCore.QCoreApplication.processEvents()
        self.textBox.moveCursor(QtGui.QTextCursor.End)
        self.textBox.insertPlainText(self.proc.readAllStandardOutput().data().decode('utf-8'))
        self.textBox.insertPlainText(self.proc.readAllStandardError().data().decode('utf-8'))
        self.textBox.moveCursor(QtGui.QTextCursor.End)
