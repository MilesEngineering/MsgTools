#!/cygdrive/c/Python34/python.exe
import sys
from PySide import QtCore, QtGui
from PySide.QtGui import *
from PySide.QtCore import Qt

# import the MsgApp baseclass, for messages, and network I/O
sys.path.append("../MsgApp")
import MsgGui

class MessageScope():