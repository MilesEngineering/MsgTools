from collections import namedtuple
import ctypes
from datetime import datetime

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
            if fromHdrInfo.timeField != None:
                # if we're converting from a header with a smaller timestamp to a header
                # with a bigger timestamp, look for wrapping of the input timestamp
                if int(fromHdrInfo.timeField.maxVal) < int(toHdrInfo.timeField.maxVal):
                    # Detect time rolling
                    thisTimestamp = fromHdr.GetTime()
                    thisTime = datetime.now()
                    if thisTimestamp < self._lastTimestamp:
                        # If the timestamp shouldn't have wrapped yet, assume messages sent out-of-order,
                        # and do not wrap again.
                        if thisTime > self.lastWrapTime.addSecs(30):
                            self.lastWrapTime = thisTime
                            self._timestampOffset += 1
                    self._lastTimestamp = thisTimestamp
                    # need to handle different size timestamps!
                    toHdr.SetTime(self._timestampOffset * (1+int(fromHdrInfo.timeField.maxVal)) + thisTimestamp)
                else:
                    toHdr.SetTime(fromHdr.GetTime())
            else:
                t = datetime.now().timestamp()
                # use time since start of day, if 32-bit or smaller timestamps
                if float(toHdrInfo.timeField.maxVal) <= 2**32:
                    t = (datetime.fromtimestamp(t) - datetime.fromtimestamp(t).replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                if toHdrInfo.timeField.units == "ms":
                    t = t * 1000.0
                if toHdrInfo.timeField.type == "int":
                    t = int(t)
                toHdr.SetTime(t)

        return toHdr

    def translate(self, fromHdr):
        toHdr = self.translateHdrAndBody(fromHdr, fromHdr.rawBuffer()[type(fromHdr).SIZE:])
        return toHdr

