import argparse
import os
import socket
import sys

if sys.version_info<(3,4):
    raise SystemExit('''\n\nSorry, this code need Python 3.4 or higher.\n
To avoid incorrectly using python2 in your path, you may want to try launching by:
    ./path/to/script/ScriptName.py
NOT
    python path/to/script/ScriptName.py\n''')

from PyQt5 import QtWidgets, QtCore
from .messaging import Messaging, TimestampFixer
from .client_connection import ClientConnection

class App(QtWidgets.QMainWindow):
    RxMsg = QtCore.pyqtSignal(object)
    statusUpdate = QtCore.pyqtSignal(str)
    connectionChanged = QtCore.pyqtSignal(bool)

    @classmethod
    def addBaseArguments(cls, parser):
        '''
        Adds base app arguments to the provided ArgParser
        skipFiles - if True we won't provide an agument for a files list
        returns the parser
        '''
        parser.add_argument('--connectionName', default='127.0.0.1:5678',
            help='''The connection name.  For socket connections this is an IP and port e.g. 127.0.0.1:5678.  
                    You may prepend ws:// to indicate you want to use a Websocket instead.  For file 
                    connection types, this is the filename to use as a message source.
                    This parameter is overridden by the --ip and --port options.''')
        parser.add_argument('--ip', help='The IP address for a socket connection.   Overrides connectionName.')
        parser.add_argument('--port', type=int, help='The port for a socket connection. Overrides connectionName.')
        parser.add_argument('--msg', nargs='+', default=set(), help='''A space delimited list of white list messages to process.
                    All messages outside of this list will be ignored.  For example: --msg TestCase1 Network.Note 
                    Taxonomy/Candidae.AFox''')
        parser.add_argument('--msgdir', help=''''The directory to load Python message source from.''')
        parser.add_argument('--serial', action='store_true', help='Set if you want to use a SerialHeader instead of a NetworkHeader.')
        parser.add_argument('--log', help='The log file type (csv/json/bin) or complete log file name.')

        return parser
    
    def __init__(self, name, args):
        '''Initializer - this is used more as a decorator in the MsgTools suite than an actual
        standalone class.

        name - the name of the application - usually displayed in the UI window header
        args - argparse.Namespace of command line options.  See getArgParser for what we provide
               by default as part of this base app framework.  A command line tool may act as a 
               parent ArgumentParser and provide additional options.
        '''

        # If the caller skips adding base arguments we need to patch up args
        args.serial = None if hasattr(args, 'serial') == False else args.serial
        args.msg = None if hasattr(args, 'msg') == False else args.msg
        args.msgdir = None if hasattr(args, 'msgdir') == False else args.msgdir

        self.name = name
        
        # persistent settings
        self.settings = QtCore.QSettings("MsgTools", name)
        
        self.allowedMessages = set(args.msg)
        
        # flag that indicates if we're connected
        self.connected = False
        
        # directory to load messages from.
        msgLoadDir = None

        # Set default that can be overridden by command line arguments.
        ip = "127.0.0.1"
        port = 5678

        if args.connectionName is not None:
            self.connectionName = args.connectionName
        if args.ip is not None:
            ip = args.ip
        if args.msgdir:
            msgLoadDir = args.msgdir
            self.msgdir = args.msgdir
        
        # if either --ip or --port were used, override connectionName
        if args.ip is not None or args.port is not None:
            if args.ip is not None:
                ip = args.ip
            if args.port is not None:
                port = args.port
            self.connectionName = "%s:%s" % (ip, port)

        try:
            Messaging.LoadAllMessages(searchdir=msgLoadDir, headerName="NetworkHeader")
        except RuntimeError as e:
            print(e)
            quit()
        except:
            import traceback
            print(traceback.format_exc())
            quit()

        if args.msg is not None:
            # Validate all message names are valid
            for msg in args.msg:
                if msg not in Messaging.MsgIDFromName:
                    print('{0} is not a valid message name!'.format(msg))
                    sys.exit(1)

        # object to fix timestamps of messages with no timestamp set
        self.timestamp_fixer = TimestampFixer()

        self.logFileType = None
        self.logFile = None
        if args.log is not None:
            self.startLog(args.log)

        self.connection = ClientConnection(Messaging.hdr)
        self.connection.connection_error.connect(self.displayConnectError)
        self.connection.on_connect.connect(self.onConnected)
        self.connection.on_disconnect.connect(self.onDisconnect)
        self.connection.rx_msg.connect(self.MaybeRxMsg)
        self.connection.OpenConnection(self.connectionName)

    def CloseConnection(self):
        self.connection.CloseConnection()

    def OpenConnection(self):
        self.CloseConnection()
        self.connection.OpenConnection(self.connectionName)

    def startLog(self, log_name, log_suffix=''):
        # hash table of booleans for if each type of message has had it's header
        # put into this log file already.
        self.loggedMsgHeader = {}
        if log_name.endswith('csv'):
            self.logFileType = "csv"
        elif log_name.endswith('json'):
            self.logFileType = "json"
        elif log_name.endswith('bin') or log_name.endswith('log'):
            self.logFileType = "bin"
        else:
            print("ERROR!  Invalid log type " + log_name)
        if "." in log_name:
            # if there's a ., assume they specified an exact filename to use
            logFileName = log_name
        else:
            # if not, generate a filename based on current date/time
            currentDateTime = QtCore.QDateTime.currentDateTime()
            logFileName = currentDateTime.toString("yyyyMMdd-hhmmss") + log_suffix + "." + self.logFileType
        self.logFile = QtCore.QFile(logFileName)
        self.logFile.open(QtCore.QIODevice.Append)

    def stopLog(self):
        if self.logFile is not None:
            self.logFile.close()
            self.logFile = None

    def onConnected(self):
        self.connected = True
        self.connectionChanged.emit(True)
        # send a connect message
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName(self.name)
        self.SendMsg(connectMsg)
        # if the app has it's own function to happen after connection, assume it will set subscriptions to what it wants.
        try:
            fn = self.onAppConnected
        except AttributeError:
            # send a subscription message
            subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
            self.SendMsg(subscribeMsg)
            #self.statusUpdate.emit('Connected')
        else:
            self.onAppConnected()
    
    def onDisconnect(self):
        self.connected = False
        self.connectionChanged.emit(False)
        #self.statusUpdate.emit('NOT Connected')
    
    def displayConnectError(self, socketError):
        self.connected = False
        self.connectionChanged.emit(False)
        self.statusUpdate.emit('Not Connected('+str(socketError)+'), '+self.connection.connection.errorString())

    def MaybeRxMsg(self, msg):
        '''Check msg against the list of allowed messages.
        Accept if all messages are allowed, or the message is
        in the message white list.'''
        if len(self.allowedMessages) > 0:
            if not msg.MsgName() in self.allowedMessages:
                return
        self.RxMsg.emit(msg)
        self.logMsg(msg)
    
    def SendMsg(self, msg):
        self.connection.SendMsg(msg)
        # Log all sent messages
        self.logMsg(msg)

    def logMsg(self, msg):
        if self.logFile:
            original_timestamp = self.timestamp_fixer.fix_timestamp(msg.hdr)
            log = ''
            if self.logFileType == "csv":
                if not msg.MsgName() in self.loggedMsgHeader:
                    self.loggedMsgHeader[msg.MsgName()] = True
                    log = msg.csvHeader(timeColumn=True)+'\n'
                log += msg.toCsv(timeColumn=True)+'\n'
                log = log.encode('utf-8')
            elif self.logFileType == "json":
                if not msg.MsgName() in self.loggedMsgHeader:
                    self.loggedMsgHeader[msg.MsgName()] = True
                    log = msg.jsonHeader()
                log += msg.toJson(includeHeader=True)+'\n'
                log = log.encode('utf-8')
            elif self.logFileType == "bin":
                log = msg.rawBuffer().raw
            self.logFile.write(log)
            self.logFile.flush()
            self.timestamp_fixer.restore_timestamp(msg.hdr, original_timestamp)
