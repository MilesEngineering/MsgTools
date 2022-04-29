#!/usr/bin/en"v python3
from PyQt5 import QtCore, QtGui, QtWidgets
import can
import ctypes

from msgtools.lib.messaging import Messaging, FieldInfo, offset, size
from msgtools.lib.header_translator import HeaderTranslator
from msgtools.server import CanPortDialog
import struct
import sys
import time

def hexbytes(d):
    bytes_per_line = 8
    ret = "%d\n" % len(d)
    bytes = 0
    while bytes < len(d):
        ret += ":".join("{:02X}".format(c) for c in d[bytes:bytes+bytes_per_line]) + "\n"
        bytes += bytes_per_line
    return ret

def Crc16(data):
    crc = 0;
    for i in range(0,len(data)):
        d = struct.unpack_from('B', data, i)[0]
        crc = (crc >> 8) | (crc << 8)
        crc ^= d
        crc ^= (crc & 0xff) >> 4
        crc ^= crc << 12
        crc = 0xFFFF & crc
        crc ^= (crc & 0xff) << 5
        crc = 0xFFFF & crc
    return crc

class CanFragmentation(QtCore.QObject):
    statusUpdate = QtCore.pyqtSignal(str)

    MAX_MSG_SIZE = 64
    MAX_PACKET_SIZE = MAX_MSG_SIZE
    MAX_FRAG_PACKET_SIZE = MAX_MSG_SIZE
    MAX_FRAG_FIRST_PACKET_SIZE = MAX_MSG_SIZE

    # DLC length coding
    DLC_LENGTH_CODING = [
        0, 1, 2, 3, 4, 5, 6, 7, 8,
        12, # 9
        16, # 10
        20, # 11
        24, # 12
        32, # 13
        48, # 14
        64  # 15
    ]

    DLC_FROM_LENGTH = [
        0,1,2,3,4,5,6,7,8,
        9,9,9,9, # 9-12
        10,10,10,10, # 13-16
        11,11,11,11, # 17-20
        12,12,12,12, # 21-24
        13,13,13,13,13,13,13,13, # 25-32
        14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14, # 33-48
        15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15  # 49-64
    ]
    
    @staticmethod
    def length_decrement(packet_len):
        #print("%d / %d" % (packet_len, len()
        return CanFragmentation.DLC_LENGTH_CODING[CanFragmentation.DLC_FROM_LENGTH[packet_len]] - packet_len

    @staticmethod
    def packet_count(msg_len):
        if msg_len <= CanFragmentation.MAX_PACKET_SIZE:
            return 1
        total_bytes_for_frag_packets = msg_len+(CanFragmentation.MAX_FRAG_PACKET_SIZE-CanFragmentation.MAX_FRAG_FIRST_PACKET_SIZE)
        return int(total_bytes_for_frag_packets / CanFragmentation.MAX_FRAG_PACKET_SIZE) + (total_bytes_for_frag_packets % CanFragmentation.MAX_FRAG_PACKET_SIZE > 0)

    def __init__(self):
        super(CanFragmentation, self).__init__(None)

        import CANHeader
        # Make a subclass of CANHeader that acts like it has a "DataLength".
        # The real CAN header doesn't have a DataLength, it instead has a "DLC"
        # (which for CAN FD is larger than the actual length of the message body),
        # and a LengthDecrement field which is how much smaller the real length
        # is than is indicated by DLC.
        class CANHeaderWithLength(CANHeader.CANHeader):
            def __init__(self, messageBuffer=None):
                super(CANHeaderWithLength, self).__init__(messageBuffer)
                self.length = -1
            @offset('-1')
            @size('0')
            def GetDataLength(self):
                #print("  CANHeaderWithLength.GetDataLength() = %d" % self.length)
                return self.length
            def SetDataLength(self, l):
                self.length = l
                #print("  CANHeaderWithLength.SetDataLength(%d)" % self.length)
        CANHeaderWithLength.fields.append(
            FieldInfo(name="DataLength",type="int",units="",minVal="0",maxVal="65535",description="Length of CAN Message.",get=CANHeaderWithLength.GetDataLength,set=CANHeaderWithLength.SetDataLength,count=1, bitfieldInfo = [], enum = [])
        )
        
        # If fragmentation headers exist, use them to perform fragmentation and reassembly of CAN messages.
        try:
            self.frag_hdr = CANHeader.FragmentationHeader
            self.frag_hdr_start = CANHeader.FragmentationHeaderStart

        except AttributeError:
            self.frag_hdr = None
            self.frag_hdr_start = None
        if self.frag_hdr and self.frag_hdr_start:
            # find bytes in most fragmented packets by taking max size and subtracting size of fragmentation header
            CanFragmentation.MAX_FRAG_PACKET_SIZE = CanFragmentation.MAX_PACKET_SIZE - self.frag_hdr.SIZE
            # find bytes in first fragmented packet by also subtracting size of the fragmentation 'start' header
            CanFragmentation.MAX_FRAG_FIRST_PACKET_SIZE = CanFragmentation.MAX_FRAG_PACKET_SIZE - self.frag_hdr_start.SIZE
            # total size is size of first frag packet, plus all the other fragmented packets.
            max_packets = int(self.frag_hdr.GetSequenceNumber.maxVal)
            CanFragmentation.MAX_MSG_SIZE = CanFragmentation.MAX_FRAG_FIRST_PACKET_SIZE + (max_packets-1)* CanFragmentation.MAX_FRAG_PACKET_SIZE

        self.hdr = CANHeaderWithLength

        self.hdrTranslator = HeaderTranslator(self.hdr, Messaging.hdr)

        self.frag_stream_id = 0
        
        self.use_print = False
        
        self.in_progress_reassembly = {}

    def print(self, s):
        if self.use_print:
            print("F: " + s)
        else:
            self.statusUpdate.emit("Fragmentation: "+s)

    def fragment(self, networkMsg):
        # translate the header
        canHdr = self.hdrTranslator.translateHdr(networkMsg)
        # if we can't translate the header, just return because the message can't be sent on CAN
        if canHdr == None:
            if Messaging.debug:
                self.print("Can't translate 0x%x to CAN message" % networkMsg.GetMessageID())
            return []

        # check that the message fits
        if networkMsg.GetDataLength() > CanFragmentation.MAX_MSG_SIZE:
            if Messaging.debug:
                self.print("Message 0x%x size %d > %d bytes, too big for CAN" % (networkMsg.GetMessageID(), networkMsg.GetDataLength(), CanFragmentation.MAX_MSG_SIZE))
            return []

        packets = []
        
        bytes_sent = 0
        packets_sent = 0
        msg_len = networkMsg.GetDataLength()
        max_packets = CanFragmentation.packet_count(msg_len)
        #self.print("\nmsg_len: %d\nmax_packets: %d\n" % (msg_len, max_packets))
        data_ptr = networkMsg.rawBuffer()[type(networkMsg).SIZE:]
        while bytes_sent < msg_len:
            if max_packets == 1:
                max_packet_size = CanFragmentation.MAX_PACKET_SIZE
            else:
                max_packet_size = CanFragmentation.MAX_FRAG_PACKET_SIZE if bytes_sent else CanFragmentation.MAX_FRAG_FIRST_PACKET_SIZE
            packet_size = min(msg_len - bytes_sent, max_packet_size)
            #self.print("packet_size: %d, max_packet_size: %d" % (packet_size, max_packet_size))
            if max_packets > 1:
                canHdr.SetFragmented(1)
                frag_hdr = self.frag_hdr()
                frag_hdr.SetNewStream(1 if bytes_sent == 0 else 0)
                frag_hdr.SetStreamID(self.frag_stream_id)
                self.frag_stream_id += 1
                if self.frag_stream_id > int(frag_hdr.SetStreamID.maxVal):
                    self.frag_stream_id = 0
                frag_hdr.SetSequenceNumber(max_packets if bytes_sent == 0 else packets_sent)
                tx_data = frag_hdr.rawBuffer().raw
                if bytes_sent == 0:
                    frag_hdr_start = self.frag_hdr_start()
                    frag_hdr_start.SetMessageLength(msg_len)
                    frag_hdr_start.SetCRC16(Crc16(data_ptr))
                    tx_data += frag_hdr_start.rawBuffer().raw
                tx_data += data_ptr[bytes_sent:bytes_sent+packet_size]
            else:
                tx_data = data_ptr[0:packet_size]
            #self.print(hexbytes(tx_data))
            unpadded_len = len(tx_data)
            tx_data = tx_data + ctypes.create_string_buffer(CanFragmentation.length_decrement(len(tx_data)))
            tx_frame = can.Message(
                is_extended_id=True,
                is_remote_frame=False,
                is_error_frame=False,
                bitrate_switch=True,
                is_fd=True,
                data=tx_data)
            # compute the LengthDecrement after DLC is set in header based on body length,
            # and then update arbitration ID which contains LengthDecrement
            canHdr.SetLengthDecrement(CanFragmentation.length_decrement(unpadded_len))
            tx_frame.arbitration_id = canHdr.GetCanID()
            packets.append(tx_frame)
            #print("tx " + str(tx_frame))
            #print("sent %d/%d/%d of %d/%d (%d)" % (packet_size, unpadded_len, len(tx_data), bytes_sent, networkMsg.GetDataLength(), canHdr.GetLengthDecrement()))
            bytes_sent += packet_size
            packets_sent += 1
        return packets
    
    def reassemble(self, rx_frame):
        class ReassemblyProgress:
            def __init__(self, networkMsg, rx_byte_count, last_time):
                self.networkMsg = networkMsg
                self.rx_byte_count = rx_byte_count
                self.last_time = last_time
        
        #TODO: Need to look through in-progress table for stale partially assembled
        # messages and delete them (and probably print error messages too)
        
        # consider enforcing rules for how many in-progress messages a single source can
        # have, and throw away that source's in progress messages if too many come in with
        # unique stream IDs

        canHdr = self.hdr()
        canHdr.SetCanID(rx_frame.arbitration_id)
        canHdr.SetDataLength(len(rx_frame.data) - canHdr.GetLengthDecrement())
        #print(canHdr)
        #print("in[%d]: %s" % (canHdr.GetDataLength(), str(canHdr)))
        #print("rx " + str(rx_frame))
        if self.frag_hdr and canHdr.GetFragmented():
            frag_hdr = self.frag_hdr(rx_frame.data)
            key = "%s@%s" % (str(canHdr.GetID()), "/".join(Messaging.HeaderRoute(canHdr)))
            #print(frag_hdr)
            if frag_hdr.GetNewStream():
                packet_count = frag_hdr.GetSequenceNumber()
                frag_hdr_start = self.frag_hdr_start(rx_frame.data[self.frag_hdr.SIZE:])
                
                packet_data = rx_frame.data[self.frag_hdr.SIZE+self.frag_hdr_start.SIZE:canHdr.GetDataLength()]
                #print("Adding %d/%d/%d to %d/%d (%d)" % (len(packet_data), canHdr.GetDataLength(), len(rx_frame.data), 0, frag_hdr_start.GetMessageLength(), canHdr.GetLengthDecrement()))
                #print(frag_hdr_start)
                #print("Making %d byte body with %d bytes to start" % (frag_hdr_start.GetMessageLength(), len(packet_data)))
                canHdr.SetDataLength(frag_hdr_start.GetMessageLength())
                #print("->")
                networkMsg = self.hdrTranslator.translateHdr(canHdr)
                #print("<-")
                if networkMsg:
                    #print(networkMsg)
                    # copy packet body into message buffer
                    rx_byte_count=0
                    for b in packet_data:
                        networkMsg.rawBuffer()[type(networkMsg).SIZE+rx_byte_count] = b
                        rx_byte_count += 1
                    self.in_progress_reassembly[key] = ReassemblyProgress(networkMsg,rx_byte_count,time.time())
                    #print("Stored %d bytes for network msg %s" % (rx_byte_count, str(networkMsg)))
            else:
                packet_data = rx_frame.data[self.frag_hdr.SIZE:canHdr.GetDataLength()]
                if key in self.in_progress_reassembly:
                    progress = self.in_progress_reassembly[key]
                    #print("Adding %d/%d/%d to %d/%d (%d)" % (len(packet_data), canHdr.GetDataLength(), len(rx_frame.data), progress.rx_byte_count, progress.networkMsg.GetDataLength(), canHdr.GetLengthDecrement()))
                    for b in packet_data:
                        if progress.rx_byte_count > progress.networkMsg.GetDataLength():
                            self.print("ERROR!  On byte %d/%d but only have room for %d" % (progress.rx_byte_count, len(packet_data), progress.networkMsg.GetDataLength()))
                        progress.networkMsg.rawBuffer()[type(progress.networkMsg).SIZE+progress.rx_byte_count] = b
                        progress.rx_byte_count += 1
                    #print("Found network header " + str(progress.networkMsg))
                    #print("Got to %d/%d bytes!" % (progress.rx_byte_count, progress.networkMsg.GetDataLength()))
                    if progress.rx_byte_count >= progress.networkMsg.GetDataLength():
                        #print("Reassembled a msg!!")
                        self.in_progress_reassembly.pop(key)
                        return progress.networkMsg
                    #else:
                    #    print("Have %d/%d" % (progress.rx_byte_count, progress.networkMsg.GetDataLength()))
        else:
            #self.print("reassembling " + str(rx_frame) + hexbytes(rx_frame.data))
            #self.print("time is " + str(rx_frame.timestamp))
            networkMsg = self.hdrTranslator.translateHdrAndBody(canHdr, rx_frame.data)
            try:
                networkMsg.SetTime(rx_frame.timestamp)
            except struct.error:
                networkMsg.SetTime(int(rx_frame.timestamp))
            return networkMsg
        return None
    
class CanConnection(QtCore.QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)

    def __init__(self):
        super(CanConnection, self).__init__(None)

        self.fragmentation = CanFragmentation()
        self.fragmentation.statusUpdate.connect(self.print)
        
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
        d.statusUpdate.connect(self.statusUpdate)
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
            networkMessage = self.fragmentation.reassemble(rx_frame)
            if networkMessage:
                self.messagereceived.emit(networkMessage)

    def sendMsg(self, networkMsg):
        if self.canPort == None:
            return
        
        can_packets = self.fragmentation.fragment(networkMsg)
        for tx_frame in can_packets:
            self.canPort.send(tx_frame)

def PluginConnection(param=None):
    return CanConnection()

def PluginEnabled():
    try:
        from CANHeader import CANHeader
        return True
    except:
        return False


import collections
PluginInfo = collections.namedtuple('PluginInfo', ['name', 'enabled', 'connect_function'])
plugin_info = PluginInfo('CAN', PluginEnabled, PluginConnection)
