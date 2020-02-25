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
        
        # this is a trick to allow the creation of fake fields that aren't actually in a message,
        # but that we want to act like fields of the message
        self.fake_fields = {}

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
        elif attr in self.fake_fields:
            return self.fake_fields[attr]
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
        allowed_attributes = ['msg_buffer_wrapper', 'hdr', 'fake_fields']
        if attr in allowed_attributes:
            super(Message, self).__setattr__(attr, val)
        else:
            raise AttributeError('Message %s has no field %s' % (self.MsgName(), attr))

# these could be installed by monkey patching the Message class, when msgjson.py or msgcsv.py is imported!
# doing that would prevent the dependency of this file importing msgjson and msgcsv, but would still
# allow easy conversion of messages to/from CSV and JSON, if those files are imported elsewhere.
# it would also extend to other conversions, like protobufs for example
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
    
    # we should add support for msgname(p1,p2,p3, [p4a, p4b, p4c])
    # and also msgname(f1=p1, f3=p3, f4=[p4a, p4b, p4c], f2=p2)
    # it'll be useful because it's the exact same syntax as the message constructor takes,
    # so will make it possible for the msgtools.lib.gui.LineEditWithHistory to use same
    # syntax as python scripts do.  it also matches what Message.__str__ outputs.
    
    # alternatively, should we have one fromStr function that accepts all of:
    # 1) json
    # 2) csv
    # 3) string that works as python object constructor
    # ?
    @staticmethod
    def fromStr(s):
        pass

    def toJson(self, includeHeader=False):
        return msgjson.toJson(self, includeHeader)

    def toCsv(self, nameColumn=True, timeColumn=False):
        return msgcsv.toCsv(self, nameColumn=nameColumn, timeColumn=timeColumn)
    
    def csvHeader(self, nameColumn=True, timeColumn=False):
        return msgcsv.csvHeader(self, nameColumn=nameColumn, timeColumn=timeColumn)

    def __repr__(self):
        def add_param(n, v):
            if v == '':
                v = '""'
            if ',' in v and not((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                v = '"%s"' % v
            return n + " = " + v + ", "
        ret = ''
        for fieldInfo in self.fields:
            if(fieldInfo.count == 1):
                if not fieldInfo.exists(self):
                    break
                if len(fieldInfo.bitfieldInfo) == 0:
                    ret += add_param(fieldInfo.name, str(Messaging.get(self, fieldInfo)))
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        ret += add_param(bitInfo.name, str(Messaging.get(self, bitInfo)))
            else:
                arrayList = []
                terminate = 0
                for i in range(0,fieldInfo.count):
                    if not fieldInfo.exists(self, i):
                        terminate = 1
                        break
                    arrayList.append(str(Messaging.get(self, fieldInfo, i)))
                ret += add_param(fieldInfo.name, "[" + ','.join(arrayList) + "]")
                if terminate:
                    break

        if ret.endswith(", "):
            ret = ret[:-2]
        return "%s(%s)" % (self.MsgName(), ret)
