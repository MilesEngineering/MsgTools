import ctypes
from msgtools.lib.messaging import *
import msgtools.lib.msgjson as msgjson
import msgtools.lib.msgcsv as msgcsv

class Message:
    def __init__(self, messageBuffer=None, id=None, size=None):
        doInit = 0
        if messageBuffer == None:
            doInit = 1
            messageBuffer = ctypes.create_string_buffer(Messaging.hdrSize + size)
        else:
            try:
                messageBuffer.raw
            except AttributeError:
                newbuf = ctypes.create_string_buffer(len(messageBuffer))
                for i in range(0, len(messageBuffer)):
                    newbuf[i] = bytes(messageBuffer)[i]
                messageBuffer = newbuf
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        self.msg_buffer_wrapper = { "msg_buffer": messageBuffer }

        self.hdr = Messaging.hdr(messageBuffer)

        if doInit:
            self.hdr.SetMessageID(id)
            self.hdr.SetDataLength(size)

    def rawBuffer(self):
        # this is a trick to get us to store a copy of a pointer to a buffer, rather than making a copy of the buffer
        return self.msg_buffer_wrapper["msg_buffer"]

    def set_fields(self, **kwargs):
        for param, value in kwargs.items():
            fn = getattr(self, "Set"+param)
            if fn.count > 1:
                if not isinstance(value, list):
                    value = [value]
                for idx in range(0,len(value)):
                    fn(value[idx], idx)
            else:
                fn(value)

    def __getattr__(self, attr):
        fn_name = 'Get' + attr
        if hasattr(type(self), fn_name):
            fn = getattr(self,fn_name)
            if callable(fn):
                if fn.count > 1:
                    ret = []
                    for i in range(0,fn.count):
                        try:
                            ret.append(fn(i))
                        except struct.error:
                            pass
                    return ret
                else:
                    return fn()
        raise AttributeError('Message %s has no field %s' % (self.MsgName(), attr))

    def __setattr__(self, attr, val):
        fn_name = 'Set' + attr
        if (not attr.startswith('Set')) and (not attr.startswith('Get')) and fn_name in dir(type(self)):
            fn = getattr(self,fn_name)
            if callable(fn):
                if fn.count > 1:
                    if not isinstance(val, list):
                        raise AttributeError('Message %s field %s needs array param, not %s' % (self.MsgName(), attr, str(val)))
                    for i in range(0,len(val)):
                        try:
                            fn(val[i], i)
                        except struct.error:
                            break
                    return
                else:
                    fn(val)
                    return
        allowed_attributes = ['msg_buffer_wrapper', 'hdr']
        if attr in allowed_attributes:
            super(Message, self).__setattr__(attr, val)
        else:
            raise AttributeError('Message %s has no field %s' % (self.MsgName(), attr))

# these can be installed by monkey patching the Message class, when msgjson.py or msgcsv.py is imported!
#   Message.fromJson = msgjson.jsonToMsg
#   Message.fromCsv  = msgcsv.csvToMsg
#   Message.toJson   = msgjson.toJson
#   Message.toCsv    = msgcsv.toCsv

    @staticmethod
    def fromJson(s):
        return msgjson.jsonToMsg(s)

    @staticmethod
    def fromCsv(s):
        return msgcsv.csvToMsg(s)

    def toJson(self):
        return msgjson.toJson(self)

    def toCsv(self):
        return msgjson.toCsv(self)
