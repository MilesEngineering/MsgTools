# Used to display fields of an unknown message
import struct
import ctypes
from msgtools.lib.messaging import *
import msgtools.lib.messaging as msg

class UnknownMsg :
    MSG_OFFSET = Messaging.hdrSize
    
    def __init__(self, messageBuffer):
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        self.msg_buffer_wrapper = { "msg_buffer": messageBuffer }

        self.hdr = Messaging.hdr(messageBuffer)

    # This is a hack to make UnknownMsgs appear to have a ID property
    def __getattr__(self, attr):
        if attr == 'ID':
            return self.hdr.GetMessageID()
        return getattr(self, attr)

    def rawBuffer(self):
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        return self.msg_buffer_wrapper["msg_buffer"]

    def MsgName(self):
        id = hex(self.hdr.GetMessageID())
        return "Unknown_"+id

    @msg.offset('0')
    @msg.size('64')
    def GetRawData(self, index):
        """"""
        value = struct.unpack_from('>B', self.rawBuffer(), UnknownMsg.MSG_OFFSET + index)[0]
        return hex(value)
        
    @msg.offset('0')
    @msg.size('64')
    def SetRawData(self, value, index):
        """"""
        struct.pack_into('>B', self.rawBuffer(), UnknownMsg.MSG_OFFSET + index, value)
    
    # Reflection information
    fields = [FieldInfo(name="rawData",type="int",units="",minVal="",maxVal="",description="",get=GetRawData,set=SetRawData,count=64, bitfieldInfo = [], enum = [])]
