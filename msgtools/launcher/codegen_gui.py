import sys
import subprocess
import os

from PyQt5 import QtCore, QtGui, QtWidgets

base_dir = "/opt/msgtools"
msg_dir = base_dir + "/messages"
obj_dir = base_dir + "/obj/CodeGenerator"

class CodegenGui(QtCore.QObject):
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
        languages = self.language_options()
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
        self.build(self.selectedLanguages)

    def codegen_clean(self):
        self.clean()
        
    def build(self, languageNames):
        commands = []
        for languageName in languageNames:
            languageOptions = self.languageOptions[languageName]
            languagePluginName = languageOptions[0]
            outputDir = obj_dir + '/' + languageOptions[1]
            invoke = 'msgparser %s %s %s' % (msg_dir, outputDir, languagePluginName)
            commands.append(invoke)
        self.invoke(commands)

    def clean(self):
        self.invoke(['rm -rf %s' % obj_dir])

    def language_options(self):
        return self.languageOptions.keys()

    def invoke(self, commands):
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
        self.textBox.insertPlainText('> %s\n' % command)
        self.textBox.moveCursor(QtGui.QTextCursor.End)
        self.proc = QtCore.QProcess(self)
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
