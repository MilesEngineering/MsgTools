# Used to display fields of an unknown message
import struct
import ctypes
from Messaging import *
import Messaging as msg

class UnknownMsg :
    MSG_OFFSET = Messaging.hdrSize
    
    def __init__(self, messageBuffer):
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        self.msg_buffer_wrapper = { "msg_buffer": messageBuffer }

        self.hdr = Messaging.hdr(messageBuffer)

    def rawBuffer(self):
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        return self.msg_buffer_wrapper["msg_buffer"]

    def MsgName():
        id = hex(self.hdr.GetMessageID())
        return "Unknown_"+id

    def GetRawData(index):
        """"""
        value = struct.unpack_from('>B', self.rawBuffer(), UnknownMsg.MSG_OFFSET + index)[0]
        return hex(value)
        
    def SetRawData(value, index):
        """"""
        struct.pack_into('>B', self.rawBuffer(), UnknownMsg.MSG_OFFSET + index, value)
    
    # Reflection information
    fields = [FieldInfo(name="rawData",type="int",units="",minVal="",maxVal="",description="",get=GetRawData,set=SetRawData,count=64, bitfieldInfo = [], enum = [])]
