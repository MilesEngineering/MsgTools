# Used to display fields of an unknown message
import struct
import ctypes
from Messaging import *
import Messaging as msg

class UnknownMsg :
    MSG_OFFSET = Messaging.hdrSize
    
    @staticmethod
    def GetRawData(message_buffer, index):
        """"""
        value = struct.unpack_from('>B', message_buffer, UnknownMsg.MSG_OFFSET + index)[0]
        return value
        
    @staticmethod
    def SetRawData(message_buffer, value, index):
        """"""
        struct.pack_into('>B', message_buffer, UnknownMsg.MSG_OFFSET + index, value)
    
    # Reflection information
    fields = [FieldInfo(name="rawData",type="int",units="",minVal="",maxVal="",description="",get=GetRawData,set=SetRawData,count=64, bitfieldInfo = [], enum = [])]
