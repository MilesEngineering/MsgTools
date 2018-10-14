from PyQt5 import QtGui
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

class EditWindow(QsciScintilla):
    CRASH_MARKER_NUM = 7
    DEBUG_MARKER_NUM = 8
    EXEC_MARKER_NUM = 9

    def __init__(self, parent=None):
        super(EditWindow, self).__init__(parent)
        
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
        
        # debug marker
        self.markerDefine(QsciScintilla.Circle, self.DEBUG_MARKER_NUM)
        self.setMarkerBackgroundColor(QtGui.QColor("#1111ee"), self.DEBUG_MARKER_NUM)

        # execute marker
        self.markerDefine(QsciScintilla.Circle, self.EXEC_MARKER_NUM)
        self.setMarkerBackgroundColor(QtGui.QColor("#11ee11"), self.EXEC_MARKER_NUM)

        # crash marker
        self.markerDefine(QsciScintilla.Circle, self.CRASH_MARKER_NUM)
        self.setMarkerBackgroundColor(QtGui.QColor("#ee1111"), self.CRASH_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#ffe4e4"))

        # Set Python lexer
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)

        text = bytearray(str.encode("Arial"))
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, text)

        # not too small
        self.setMinimumSize(600, 450)
        
        self.last_exec_line = 0

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle debug marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.DEBUG_MARKER_NUM)
        else:
            self.markerAdd(nline, self.DEBUG_MARKER_NUM)
            
    def exited(self):
        markerBitmask = self.markersAtLine(self.last_exec_line)
        if (1 << self.EXEC_MARKER_NUM) & markerBitmask:
            self.markerDelete(self.last_exec_line, self.EXEC_MARKER_NUM)
        self.markerAdd(self.last_exec_line, self.CRASH_MARKER_NUM)

    def crashed(self):
        markerBitmask = self.markersAtLine(self.last_exec_line)
        if (1 << self.EXEC_MARKER_NUM) & markerBitmask:
            self.markerDelete(self.last_exec_line, self.EXEC_MARKER_NUM)
        self.markerAdd(self.last_exec_line, self.CRASH_MARKER_NUM)

    # function called to indicate we executed up to a line of code
    def ran_to_line(self, nline):
        # change line number to zero based indexing
        nline = nline - 1
        markerBitmask = self.markersAtLine(self.last_exec_line)
        if (1 << self.EXEC_MARKER_NUM) & markerBitmask:
            self.markerDelete(self.last_exec_line, self.EXEC_MARKER_NUM)
        if (1 << self.CRASH_MARKER_NUM) & markerBitmask:
            # We have to delete crash marker twice!  Dunno why!
            self.markerDelete(self.last_exec_line, self.CRASH_MARKER_NUM)
            self.markerDelete(self.last_exec_line, self.CRASH_MARKER_NUM)
        if nline >= 0:
            self.markerAdd(nline, self.EXEC_MARKER_NUM)
            self.last_exec_line = nline
    
    def has_breakpoint(self, nline):
        # change line number to zero based indexing
        nline = nline - 1
        markerBitmask = self.markersAtLine(self.last_exec_line)
        if (1 << self.DEBUG_MARKER_NUM) & markerBitmask:
            return True
        return False
