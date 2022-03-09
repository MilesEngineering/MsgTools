#!/usr/bin/en"v python3
from PyQt5 import QtCore, QtGui, QtWidgets
import can

from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderTranslator
from msgtools.server import CanPortDialog
import sys

class CanConnection(QtCore.QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)

    def __init__(self, hdr):
        super(CanConnection, self).__init__(None)

        self.hdr = hdr
        
        self.hdrTranslator = HeaderTranslator(hdr, Messaging.hdr)

        self.base_name = "CAN"
        self.settings = QtCore.QSettings("MsgTools", "MessageServer/"+self.base_name)
        
        self.removeClient = QtWidgets.QPushButton("Remove")
        self.removeClient.pressed.connect(self.onDisconnected)

        # button to open/close CAN port
        self.openCloseButton = QtWidgets.QPushButton("button")
        self.openCloseButton.pressed.connect(self.openCloseSwitch)
        
        # button select new CAN port
        self.selectPortButton = QtWidgets.QPushButton("Select Port")
        self.selectPortButton.pressed.connect(self.selectPort)

        self.statusLabel = QtWidgets.QLabel()
        self.rxMsgCount = 0
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = True
        
        # default to last used port
        self.portName = self.settings.value("portName", None)
        self.interfaceName = self.settings.value("interfaceName", "socketcan")

        self.canPort = None
        self.socketReadNotifier = None
        self.socketErrorNotifier = None
        self.name = "%s.%s" % (self.interfaceName, self.portName)

        self.statusLabel.setText(self.name)
        
        self.reopenTimer = QtCore.QTimer(self)
        self.reopenTimer.setInterval(1000)
        self.reopenTimer.timeout.connect(self._openCanPort)

    def print(self, s):
        self.statusUpdate.emit("CAN: "+s)

    def onDisconnected(self):
        self.disconnected.emit(self)
    
    def onErrorOccurred(self, error):
        if error == QCanBusDevice.NoError:
            pass
        elif error == QCanBusDevice.ReadError:
            self.print("Error, Closing "+str(self.name))
            self._closeCanPort()
            # Don't restart the timer if it's active.
            # If we did, then a steady stream of errors would keep resetting
            # the timer, and it would never go off.
            if not self.reopenTimer.isActive():
                self.reopenTimer.start()
        #elif error == QCanBusDevice.: # are there any errors we should just ignore?
        #    pass

    def widget(self, index):
        if index == 0:
            return self.removeClient
        if index == 1:
            return self.openCloseButton
        if index == 2:
            return self.selectPortButton
        if index == 3:
            return self.statusLabel
        return None
    
    def _openCanPort(self):
        if self.canPort:
            # if we're already open, make sure we stop retrying to open
            self.reopenTimer.stop()
        else:
            try:
                # open the CAN bus
                self.canPort = can.Bus(channel=self.portName, interface=self.interfaceName, fd=True)
                # create a socket notifier, so we get a signal when data is ready
                self.socketReadNotifier = QtCore.QSocketNotifier(self.canPort.socket.fileno(), QtCore.QSocketNotifier.Read)
                self.socketReadNotifier.activated.connect(self.onReadReady)
                self.socketErrorNotifier = QtCore.QSocketNotifier(self.canPort.socket.fileno(), QtCore.QSocketNotifier.Exception)
                self.socketErrorNotifier.activated.connect(self.onReadError)
                
                self.print("Opened "+self.name)
                self.openCloseButton.setText("Close")
                self.settings.setValue("portName", self.portName)
                self.settings.setValue("interfaceName", self.interfaceName)
                self.reopenTimer.stop()
                return True
            except Exception as ex:
                if type(ex) == ValueError:
                    self.print("Parameters are out of range")
                elif type(ex) == can.CanInterfaceNotImplementedError:
                    self.print("The driver cannot be accessed")
                elif type(ex) == can.CanInitializationError:
                    self.print("The bus cannot be initialized")
                else:
                    self.print(str(ex))
                self.canPort = None
                self._closeCanPort()
                return False

    def _closeCanPort(self):
        if self.canPort:
            self.canPort.shutdown()
            self.canPort = None
            self.socketReadNotifier = None
            self.socketErrorNotifier = None
        self.openCloseButton.setText("Open")

    def openCloseSwitch(self):
        # open or close the port
        if self.canPort:
            self._closeCanPort()
            self.print("Closed "+self.name)
        else:
            if not self._openCanPort():
                self.print("Can't open "+self.name+"!")

    def portChanged(self, interface, channel):
        self.interfaceName = interface
        self.portName = channel
        self.name = "%s.%s" % (self.interfaceName, self.portName)
        if self.canPort:
            self._closeCanPort()
        self.statusLabel.setText(self.name)
        self.openCloseSwitch()

    def selectPort(self):
        d = CanPortDialog.SelectCanPortDialog()
        d.portChanged.connect(self.portChanged)
        d.exec_()

    def start(self):
        self.openCloseSwitch()

    # need to connect something to this
    def onReadError(self, errType):
        self.print("RX " + errType)

    def stop(self):
        pass

    def onReadReady(self):
        while self.canPort:
            # Read data with zero timeout
            rx_frame = self.canPort.recv(timeout=0.0)
            # if no data, break
            if rx_frame == None:
                break
            canHdr = self.hdr()
            canHdr.SetCanID(rx_frame.arbitration_id)
            canHdr.SetDataLength(len(rx_frame.data()) - canHdr.getLengthDecrement())
            networkMsg = self.hdrTranslator.translateHdrAndBody(canHdr, rx_frame.data)
            networkMsg.SetTimestamp(rx_frame.timeStamp())
            self.messagereceived.emit(networkMsg)

    def sendMsg(self, networkMsg):
        if self.canPort == None:
            return
        # only send messages that fit in one CAN FD packet
        if networkMsg.GetDataLength() > 64:
            if Messaging.debug:
                self.print("Throwing away %d byte message 0x%x for CAN bus" % (networkMsg.GetDataLength(), networkMsg.GetMessageID()))
            return
        canMsg = self.hdrTranslator.translateHdr(networkMsg)
        # if we can't translate the header, just return
        if canMsg == None:
            if Messaging.debug:
                self.print("Can't translate 0x%x to CAN message" % networkMsg.GetMessageID())
            return
        tx_frame = can.Message(
            is_extended_id=True,
            is_remote_frame=False,
            is_error_frame=False,
            bitrate_switch=True,
            is_fd=True,
            data=networkMsg.rawBuffer().raw)
        # compute the LengthDecrement after DLC is set in header based on body length,
        # and then update arbitration ID which contains LengthDecrement
        canMsg.SetLengthDecrement(len(tx_frame.data) - networkMsg.GetDataLength())
        tx_frame.arbitration_id = canMsg.GetCanID()
        self.canPort.send(tx_frame)

def PluginConnection(param=None):
    from CANHeader import CANHeader
    # Make a subclass of CANHeader that acts like it has a "DataLength".
    # The real CAN header doesn't have a DataLength, it instead has a "DLC"
    # (which for CAN FD is larger than the actual length of the message body),
    # and a LengthDecrement field which is how much smaller the real length
    # is than is indicated by DLC.
    class CANHeaderWithLength(CANHeader):
        def __init__(self, messageBuffer=None):
            super(CANHeaderWithLength, self).__init__(messageBuffer)
            self.length = None
        def GetDataLength(self):
            return self.length
        def SetDataLength(self, l):
            self.length = l

    return CanConnection(CANHeaderWithLength)

def PluginEnabled():
    try:
        from CANHeader import CANHeader
        return True
    except:
        return False


import collections
PluginInfo = collections.namedtuple('PluginInfo', ['name', 'enabled', 'connect_function'])
plugin_info = PluginInfo('CAN', PluginEnabled, PluginConnection)
