from collections import namedtuple
import ctypes
import datetime
import struct

from .messaging import Messaging

class HeaderTranslator:
    def __init__(self, hdr1, hdr2):
        # Make a list of fields in the headers that have matching names.
        self._correspondingFields = []
        for fieldInfo1 in hdr1.fields:
            if len(fieldInfo1.bitfieldInfo) == 0:
                fieldInfo2 = Messaging.findFieldInfo(hdr2.fields, fieldInfo1.name)
                if fieldInfo2 != None:
                    self._correspondingFields.append([fieldInfo1, fieldInfo2])
            else:
                for bitfieldInfo1 in fieldInfo1.bitfieldInfo:
                    fieldInfo2 = Messaging.findFieldInfo(hdr2.fields, bitfieldInfo1.name)
                    if fieldInfo2 != None:
                        self._correspondingFields.append([bitfieldInfo1, fieldInfo2])
        
        HdrInfo = namedtuple('HdrInfo', 'type infoIndex timeField')
        self._hdr1Info = HdrInfo(hdr1, 0, Messaging.findFieldInfo(hdr1.fields, "Time"))
        self._hdr2Info = HdrInfo(hdr2, 1, Messaging.findFieldInfo(hdr2.fields, "Time"))
        self._timestampOffset = 0
        self._lastTimestamp = 0
        self.lastWrapTime = None

    def translateHdrAndBody(self, fromHdr, body):
        # figure out which direction to translate
        if isinstance(fromHdr, self._hdr1Info.type):
            fromHdrInfo = self._hdr1Info
            toHdrInfo = self._hdr2Info
        elif isinstance(fromHdr, self._hdr2Info.type):
            fromHdrInfo = self._hdr2Info
            toHdrInfo = self._hdr1Info
        else:
            print("ERROR!  type %s is not %s or %s!" % (type(fromHdr), self._hdr1Info.type, self._hdr2Info.type))
            raise TypeError
        
        # allocate the message to translate to
        toBuffer = ctypes.create_string_buffer(toHdrInfo.type.SIZE+fromHdr.GetDataLength())
        toHdr = toHdrInfo.type(toBuffer)
        toHdr.initialize()

        # loop through fields using reflection, and transfer contents from
        # one header to the other
        for pair in self._correspondingFields:
            fromFieldInfo = pair[fromHdrInfo.infoIndex]
            toFieldInfo = pair[toHdrInfo.infoIndex]
            Messaging.set(toHdr, toFieldInfo, Messaging.get(fromHdr, fromFieldInfo))
        
        # if the message ID can't be expressed in the new header, return None,
        # because this message isn't translatable
        if fromHdr.GetMessageID() != toHdr.GetMessageID():
            if Messaging.debug:
                print("message ID 0x" + hex(fromHdr.GetMessageID()) + " translated to 0x" + hex(toHdr.GetMessageID()) + ", throwing away")
            return None
        # copy the body
        for i in range(0,fromHdr.GetDataLength()):
            toHdr.rawBuffer()[toHdr.SIZE+i] = body[i]
        
        # do special timestamp stuff to convert from relative to absolute time
        if toHdrInfo.timeField != None:
            def set_time(hdr, t):
                # This is a bit ugly, but it's hard to tell with the Time field is a float or
                # an int.  If it's an int and we give it a float, struct.error gets raised.
                try:
                    hdr.SetTime(t)
                except struct.error:
                    hdr.SetTime(int(t))
            if fromHdrInfo.timeField != None:
                def timeReallyBig(tmax):
                    if tmax == 'DBL_MAX':
                        return True
                    if tmax == 'FLT_MAX':
                        return True
                    if int(tmax) >= 2**32:
                        return True
                def timeScaling(fromUnits, toUnits):
                    if fromUnits == 'ms' and toUnits == 's':
                        return 0.001
                    if fromUnits == 's' and toUnits == 'ms':
                        return 1000.0
                    return 1.0
                time_scale = timeScaling(fromHdrInfo.timeField.units, toHdrInfo.timeField.units)
                # if we're converting from a header with a smaller timestamp to a header
                # with a bigger timestamp, look for wrapping of the input timestamp
                time_could_wrap = False
                if not timeReallyBig(fromHdrInfo.timeField.maxVal):
                    if timeReallyBig(toHdrInfo.timeField.maxVal):
                        time_could_wrap = True
                    else:
                        time_could_wrap = int(fromHdrInfo.timeField.maxVal) < int(toHdrInfo.timeField.maxVal)
                if time_could_wrap:
                    # Detect time rolling
                    thisTimestamp = fromHdr.GetTime() * time_scale
                    thisTime = datetime.datetime.now()
                    if thisTimestamp < self._lastTimestamp:
                        # If the timestamp shouldn't have wrapped yet, assume messages sent out-of-order,
                        # and do not wrap again.
                        if (self.lastWrapTime == None or
                            thisTime > self.lastWrapTime + datetime.timedelta(0,30)):
                            self.lastWrapTime = thisTime
                            self._timestampOffset += 1
                    self._lastTimestamp = thisTimestamp
                    # need to handle different size timestamps!
                    set_time(toHdr, self._timestampOffset * (1+int(fromHdrInfo.timeField.maxVal)) + thisTimestamp)
                else:
                    set_time(toHdr, fromHdr.GetTime()*time_scale)
            else:
                t = datetime.datetime.now().timestamp()
                # use time since start of day, if 32-bit or smaller timestamps
                if float(toHdrInfo.timeField.maxVal) <= 2**32:
                    t = (datetime.datetime.fromtimestamp(t) - datetime.datetime.fromtimestamp(t).replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                if toHdrInfo.timeField.units == "ms":
                    t = t * 1000.0
                if toHdrInfo.timeField.type == "int":
                    t = int(t)
                set_time(toHdr, t)

        return toHdr

    def translate(self, fromHdr):
        toHdr = self.translateHdrAndBody(fromHdr, fromHdr.rawBuffer()[type(fromHdr).SIZE:])
        if toHdr != None:
            self.promoteIdFields(toHdr)
        return toHdr

    # Handle message body ID fields by populating them in message header.
    # This is to handle systems where some message body fields are conditionally
    # used as ID fields.
    def promoteIdFields(self, hdr):
        # if any message body fields are marked as IDs, look for header fields with
        # same name if header field is zero, set it to value of body field.
        id = hdr.GetMessageID()
        keep_going = True
        while(keep_going):
            keep_going = False
            msgClass = Messaging.MsgClass(hdr)
            msg = msgClass(hdr.rawBuffer())
            for fieldInfo in msg.fields:
                if fieldInfo.idbits != 0:
                    hdrFieldInfo = Messaging.findFieldInfo(hdr.fields, fieldInfo.name)
                    if hdrFieldInfo and hdrFieldInfo.get(hdr) == 0:
                        hdrFieldInfo.set(hdr, fieldInfo.get(msg))
                        keep_going = True
