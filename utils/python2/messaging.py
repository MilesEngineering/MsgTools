# for directory listing, exit function
from __future__ import division
from __future__ import absolute_import
import os, glob, sys, struct

# for reflection/introspection (find a class's methods)
import inspect

# for conversion to JSON
from collections import OrderedDict
import json

# for reading CSV
import csv

from collections import namedtuple
import ctypes
from datetime import datetime

# A decorator to specify units for fields
def units(arg):
    def _units(fcn):
        fcn.units = arg
        return fcn
    return _units

# A decorator to specify a default value for fields
def default(arg):
    def _default(fcn):
        fcn.default = arg
        return fcn
    return _default

# A decorator to specify a count for fields
def count(arg):
    def _count(fcn):
        fcn.count = arg
        return fcn
    return _count

# A decorator to specify a byte offset for fields
def offset(arg):
    def _offset(fcn):
        fcn.offset = arg
        return fcn
    return _offset

# A decorator to specify a size in bytes for fields
def size(arg):
    def _size(fcn):
        fcn.size = arg
        return fcn
    return _size

# A decorator to specify a min for fields
def minVal(arg):
    def _minVal(fcn):
        fcn.minVal = arg
        return fcn
    return _minVal

# A decorator to specify a max for fields
def maxVal(arg):
    def _maxVal(fcn):
        fcn.maxVal = arg
        return fcn
    return _maxVal

class Messaging(object):
    hdr=None
    hdrSize=0

    # hash tables for msg lookups
    MsgNameFromID = {}
    MsgIDFromName = {}
    MsgClassFromName = {}
    # container for accessing message classes via dot notation.
    # odd, in python, that using an empty lambda expression is a suitable container
    # for this, and that some other Object doesn't work better.
    Messages = lambda: None
    
    debug=0

    def __init__(self, loaddir=None, searchdir=None, debug=0, headerName=u"NetworkHeader"):
        Messaging.debug = debug
        if loaddir:
            loadDir = loaddir
            pass
        else:
            if not searchdir or not os.path.isdir(searchdir):
                searchdir = os.getcwdu()
            loadDir = os.path.join(searchdir, u"obj/CodeGenerator/Python/")
            while not os.path.isdir(loadDir):
                lastsearchdir = searchdir
                searchdir = os.path.abspath(os.path.join(searchdir, os.pardir))
                # checking if joining with pardir returns the same dir is the easiest way to
                # determine if we're at root of filesystem
                if lastsearchdir == searchdir:
                    # if we're at root of filesystem, just give up!
                    loadDir = None
                    #print("\nERROR! Auto-generated python code not found!")
                    #print("cd to a directory downstream from a parent of obj/CodeGenerator/Python\n")
                    break
                loadDir = searchdir + u"/obj/CodeGenerator/Python/"
                if Messaging.debug:
                    print u"search for objdir in " + loadDir

        # Fix the sys path for future imports
        sys.path.append(loadDir)
        sys.path.append(unicode(loadDir)+u"/headers")
        
        # if we didn't find valid auto-generated code, this will cause an import error!
        # the fix is to point to valid auto-generated code!
        headerModule = __import__(headerName)

        # Set the global header name
        Messaging.hdr = getattr(headerModule, headerName)

        # specify our header size, to come from the generated header we imported
        Messaging.hdrSize = Messaging.hdr.SIZE

        # Normalize our load directory path, and load message modules on the path
        loadDir = os.path.normpath(loadDir)
        self.LoadDir(loadDir, loadDir)

    def LoadDir(self, loadDir, rootDir):
        for filename in os.listdir(loadDir):
            filepath = loadDir + u'/' + filename
            if os.path.isdir(filepath):
                if filename != u'headers':
                    if Messaging.debug:
                        print u"descending into directory ", filepath
                    self.LoadDir(filepath, rootDir)
            elif filename.endswith(u'.py'):
                # Build an import friendly module name
                # Could've just passed the root length to be more efficient
                # but felt the easier readability was better than the miniscule
                # performance gain we could've had
                modulename = filepath[len(rootDir)+1:]
                modulename = modulename[0:modulename.rfind(u'.py')]
                modulename = modulename.replace(os.sep, u'.')
                if Messaging.debug:
                    print u"loading module "+modulename

                __import__(modulename)

    @staticmethod
    def Register(name, id, classDef):
        u'add message to the global hash table of names by ID, and IDs by name'

        id = hex(id)
        
        if Messaging.debug:
            print u"Registering", name, u"as",id
        
        if(id in Messaging.MsgNameFromID):
            print u"WARNING! Trying to define message ", name, u" for ID ", id, u", but ", Messaging.MsgNameFromID[id], u" already uses that ID"
        
        Messaging.MsgNameFromID[id] = name

        Messaging.AddAlias(name, id, classDef)

    @staticmethod
    def AddAlias(name, id, classDef):
        u'add message to the global hash table of IDs by name'

        if(name in Messaging.MsgIDFromName):
            print u"WARNING! Trying to define message %s for ID %s(%d), but %s(%d) already uses that name" % (name, id, int(id, 0), Messaging.MsgIDFromName[name], int(Messaging.MsgIDFromName[name], 0))

        Messaging.MsgIDFromName[name] = id
        Messaging.MsgClassFromName[name] = classDef

        # split up the name between periods, and add it to the Messaging object so it
        # can be accessed via dot notation
        nameParts = name.split(u".")
        messagingVars = vars(Messaging.Messages)
        for namePart in nameParts[:-1]:
            if namePart and not namePart in messagingVars:
                messagingVars[namePart] = lambda: None
            messagingVars = vars(messagingVars[namePart])
        messagingVars[nameParts[-1]] = classDef

    @staticmethod
    def MsgFactory(msg):
        u'''Return an instance of the message class for the given message buffer.
        msg should be the full header and message payload.  Not just the header.'''
        msgClass = Messaging.MsgClass(msg)
        return msgClass(msg.rawBuffer())

    @staticmethod
    def MsgClass(hdr):
        u'''Utility method that returns the message class for the passed
        in header.'''
        msgId = hex(hdr.GetMessageID())

        if not msgId in Messaging.MsgNameFromID:
            #print("WARNING! No definition for ", msgId, "!\n")
            from msgtools.lib.unknownmsg import UnknownMsg
            msgClass = UnknownMsg
        else:
            msgName = Messaging.MsgNameFromID[msgId]
            msgClass = Messaging.MsgClassFromName[msgName]

        return msgClass


    @staticmethod
    def set(msg, fieldInfo, value, index=0):
        if(u"int" in fieldInfo.type):
            if isinstance(value, unicode):
                value = value.strip()
                if value.startswith(u"0x"):
                    value = int(value, 0)
            value = int(float(value))
        elif(u"float" in fieldInfo.type):
            value = float(value)
        
        if not hasattr(fieldInfo, u"count") or fieldInfo.count == 1:
            fieldInfo.set(msg, value)
        else:
            fieldInfo.set(msg, value, index)

    @staticmethod
    def get(msg, fieldInfo, index=0):
        try:
            if not hasattr(fieldInfo, u"count") or fieldInfo.count == 1:
                value = fieldInfo.get(msg)
            else:
                value = fieldInfo.get(msg, index)
        except struct.error:
            value = u"UNALLOCATED"
        return unicode(value)

    @staticmethod
    def getFloat(msg, fieldInfo, index=0):
        value = Messaging.get(msg, fieldInfo, index)
        if len(fieldInfo.enum) != 0:
            value = fieldInfo.enum[0].get(value, value)
        return float(value)

    @staticmethod
    def getAlert(msg, fieldInfo, index=0):
        value = Messaging.get(msg, fieldInfo, index)
        alert = 0
        try:
            floatVal = float(value)
            minVal = float(fieldInfo.minVal)
            maxVal = float(fieldInfo.maxVal)
            if(floatVal < minVal or floatVal > maxVal):
                alert = 1
        except ValueError:
            pass
        return alert

    @staticmethod
    def findFieldInfo(fieldInfos, name):
        for fi in fieldInfos:
            if len(fi.bitfieldInfo) == 0:
                if name == fi.name:
                    return fi
            else:
                for bfi in fi.bitfieldInfo:
                    if name == bfi.name:
                        return bfi
        return None

    @staticmethod
    def toJson(msg):
        msgClass = Messaging.MsgClass(msg.hdr)
        pythonObj = OrderedDict()
        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                if msg.hdr.GetDataLength() < int(fieldInfo.get.offset) + int(fieldInfo.get.size):
                    break
                if len(fieldInfo.bitfieldInfo) == 0:
                    pythonObj[fieldInfo.name] = unicode(Messaging.get(msg, fieldInfo))
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        pythonObj[bitInfo.name] = unicode(Messaging.get(msg, bitInfo))
            else:
                arrayList = []
                terminate = 0
                for i in xrange(0,fieldInfo.count):
                    if msg.hdr.GetDataLength() < int(fieldInfo.get.offset) + i*int(fieldInfo.get.size):
                        terminate = 1
                        break
                    arrayList.append(unicode(Messaging.get(msg, fieldInfo, i)))
                pythonObj[fieldInfo.name] = arrayList
                if terminate:
                    break

        return json.dumps({msg.MsgName() : pythonObj})

    @staticmethod
    def jsonToMsg(jsonString):
        terminationLen = None
        if u"hdr" in jsonString:
            fieldJson = jsonString[u"hdr"]
            for fieldName in fieldJson:
                if fieldName == u"DataLength":
                    if fieldJson[fieldName] == u";":
                        terminationLen = 0
                    else:
                        terminationLen = int(fieldJson[fieldName])
        for msgName in jsonString:
            if msgName == u"hdr":
                # hdr handled above, *before* message body
                pass
            else:
                fieldJson = jsonString[msgName]
                msgClass = Messaging.MsgClassFromName[msgName]
                msg = msgClass()
                for fieldName in fieldJson:
                    fieldInfo = Messaging.findFieldInfo(msgClass.fields, fieldName)
                    fieldValue = fieldJson[fieldName]
                    if isinstance(fieldValue, list):
                        #print(fieldName + " list type is " + str(type(fieldValue)))
                        for i in xrange(0,len(fieldValue)):
                            Messaging.set(msg, fieldInfo, fieldValue[i], i)
                            if terminationLen != None:
                                terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size)*(i+1))
                    elif isinstance(fieldValue, dict):
                        #print(fieldName + " dict type is " + str(type(fieldValue)))
                        if fieldInfo.bitfieldInfo:
                            pass
                        else:
                            pass
                    else:
                        #print(str(type(fieldValue)) + " " + fieldName + ", calling set with " + str(fieldValue))
                        Messaging.set(msg, fieldInfo, fieldValue)
                        if terminationLen != None:
                            if fieldInfo.type == u"string":
                                terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size) * len(fieldValue))
                            else:
                                terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size))
        if terminationLen != None:
            msg.hdr.SetDataLength(terminationLen)
        return msg

    @staticmethod
    def toCsv(msg):
        ret = u""
        for fieldInfo in Messaging.MsgClass(msg.hdr).fields:
            if(fieldInfo.count == 1):
                columnText = unicode(Messaging.get(msg, fieldInfo)) + u", "
                for bitInfo in fieldInfo.bitfieldInfo:
                    columnText += unicode(Messaging.get(msg, bitInfo)) + u", "
            else:
                columnText = u""
                for i in xrange(0,fieldInfo.count):
                    columnText += unicode(Messaging.get(msg, fieldInfo, i)) + u", "
            ret += columnText
        return ret

    @staticmethod
    def escapeCommasInQuotedString(line):
        ret = u""
        quoteStarted = 0
        for c in line:
            if c == u'"':
                quoteStarted = not quoteStarted
            elif c == u',':
                if quoteStarted:
                    ret = ret + u'\\'
            ret = ret + c
        return ret

    @staticmethod
    def csvToMsg(lineOfText):
        if lineOfText == u'':
            return None
        params = lineOfText.split(u" ", 1)
        msgName = params[0]
        if len(params) == 1:
            params = []
        else:
            # escape commas that are inside quoted strings
            line = Messaging.escapeCommasInQuotedString(params[1])
            # use CSV reader module
            params = list(csv.reader([line], quotechar=u'"', delimiter=u',', quoting=csv.QUOTE_NONE, skipinitialspace=True, escapechar=u'\\'))[0]
            #print("params is " + str(params))
        if msgName in Messaging.MsgClassFromName:
            msgClass = Messaging.MsgClassFromName[msgName]
            msg = msgClass()
            terminateMsg = 0
            terminationLen = 0
            if msg.fields:
                try:
                    paramNumber = 0
                    for fieldInfo in msgClass.fields:
                        val = params[paramNumber].strip()
                        #print("val is [" + val + "]") 
                        if(fieldInfo.count == 1):
                            if val.endswith(u";"):
                                terminateMsg = 1
                                val = val[:-1]
                                if val == u"":
                                    # terminate without this field
                                    terminationLen = int(fieldInfo.get.offset)
                                    break
                                # terminate after this field
                                terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size)
                            if len(fieldInfo.bitfieldInfo) == 0:
                                if fieldInfo.type == u"string":
                                    if val.startswith(u'"') and val.endswith(u'"'):
                                        val = val.strip(u'"')
                                    if terminateMsg:
                                        terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size) * len(val)
                                Messaging.set(msg, fieldInfo, val)
                                paramNumber+=1
                            else:
                                for bitInfo in fieldInfo.bitfieldInfo:
                                    Messaging.set(msg, bitInfo, val)
                                    paramNumber+=1
                                    val = params[paramNumber]
                        else:
                            if val.startswith(u"0x") and len(val) > 2+fieldInfo.count*int(fieldInfo.get.size):
                                if val.endswith(u";"):
                                    terminateMsg = 1
                                    val = val[:-1]
                                    hexStr = val[2:].strip()
                                    terminationLen = int(int(fieldInfo.get.offset) + len(hexStr)/2)
                                hexStr = val[2:].strip()
                                charsForOneElem = int(fieldInfo.get.size)*2
                                valArray = [hexStr[i:i+charsForOneElem] for i in xrange(0, len(hexStr), charsForOneElem)]
                                for i in xrange(0,len(valArray)):
                                    Messaging.set(msg, fieldInfo, int(valArray[i], 16), i)
                                paramNumber+=1
                            else:
                                for i in xrange(0,fieldInfo.count):
                                    if val.endswith(u";"):
                                        terminateMsg = 1
                                        terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size)*(i+1)
                                        val = val[:-1]
                                    Messaging.set(msg, fieldInfo, val, i)
                                    if terminateMsg:
                                        break
                                    paramNumber+=1
                                    val = params[paramNumber]
                        if terminateMsg:
                            break
                except IndexError:
                    # if index error occurs on accessing params, then stop processing params
                    # because we've processed them all
                    pass
            if terminateMsg:
                msg.hdr.SetDataLength(terminationLen)
            return msg
        else:
            #print("["+lineOfText+"] is NOT A MESSAGE NAME!")
            pass
        return None

    @staticmethod
    def long_substr(data):
        substr = u''
        if len(data) > 1 and len(data[0]) > 0:
            for j in xrange(len(data[0])-1):
                if j > len(substr) and all(data[0][0:j] in x for x in data):
                    substr = data[0][0:j]
        return substr

    @staticmethod
    def paramHelp(field):
        ret = field.name
        if field.units:
            ret = ret + u"(" + field.units + u")"
        if field.description:
            ret = ret + u"# " + field.description
        return ret

    @staticmethod
    def csvHelp(lineOfText):
        autoComplete = None
        help = u""
        params = lineOfText.split()
        if params:
            msgName = params[0]
        else:
            msgName = u''
        # if there's no params beyond first word, try to auto-complete a message name
        if len(params) <= 1 and not lineOfText.endswith(u" "):
            # search for messages that match us
            matchingMsgNames = []
            truncated = False
            for aMsgName in sorted(Messaging.MsgClassFromName.keys()):
                if aMsgName.startswith(msgName):
                    # truncate to first dot after match
                    firstdot = aMsgName.find(u'.',len(msgName))
                    if firstdot > 0:
                        aMsgName = aMsgName[0:firstdot+1]
                        truncated = True
                    if not matchingMsgNames or aMsgName != matchingMsgNames[-1]:
                        matchingMsgNames.append(aMsgName)
            if len(matchingMsgNames) == 1:
                help = matchingMsgNames[0]
                autoComplete = matchingMsgNames[0]
                # if there's only one result and we don't match it exactly (because it's longer than us)
                # accept it by giving it as autoComplete with a space at end
                #if autoComplete != msgName:
                if not truncated:
                    autoComplete = autoComplete + u' '
                return (autoComplete, help)
            else:
                help = u'\n'.join(matchingMsgNames)
                autoComplete = Messaging.long_substr(matchingMsgNames)
                #print("long_substr returned " + autoComplete)
                return (autoComplete, help)
                
        #print("param help")
        # if we didn't auto-complete a message name above, then show help on params
        paramstring = lineOfText.replace(msgName, u"",1).strip()
        params = paramstring.split(u',')
        if msgName in Messaging.MsgClassFromName:
            helpOnJustParam = len(paramstring)
            if not helpOnJustParam:
                help = msgName + u" "
            msgClass = Messaging.MsgClassFromName[msgName]
            msg = msgClass()
            if msg.fields:
                try:
                    paramNumber = 0
                    for fieldInfo in msgClass.fields:
                        if(fieldInfo.count == 1):
                            if len(fieldInfo.bitfieldInfo) == 0:
                                if helpOnJustParam:
                                    if paramNumber == len(params)-1:
                                        return (None, Messaging.paramHelp(fieldInfo))
                                    paramNumber+=1
                                else:
                                    help += fieldInfo.name + u", "
                            else:
                                for bitInfo in fieldInfo.bitfieldInfo:
                                    if helpOnJustParam:
                                        if paramNumber == len(params)-1:
                                            return (None, Messaging.paramHelp(bitInfo))
                                        paramNumber+=1
                                    else:
                                        help += bitInfo.name + u", "
                        else:
                            if helpOnJustParam:
                                arrayList = []
                                for i in xrange(0,fieldInfo.count):
                                    if helpOnJustParam and paramNumber == len(params)-1:
                                        return (None, Messaging.paramHelp(fieldInfo))
                                    paramNumber+=1
                            else:
                                help += fieldInfo.name + u"["+unicode(fieldInfo.count)+u"], "
                except IndexError:
                    # if index error occurs on accessing params, then stop processing params
                    # because we've processed them all
                    print u"done at index " + unicode(paramNumber)
                    pass
                if help.endswith(u", "):
                    help = help[:-2]
        else:
            return (None, u"["+msgName+u"] is not a message name!")
        return (autoComplete, help)

    @staticmethod
    def MsgRoute(msg):
        hdr = msg.hdr
        msg_route = []
        for fieldInfo in msg.hdr.fields:
            if fieldInfo.bitfieldInfo:
                for bitfieldInfo in fieldInfo.bitfieldInfo:
                    if bitfieldInfo.idbits == 0 and bitfieldInfo.name != u"DataLength" and bitfieldInfo.name != u"Time":
                        msg_route.append(unicode(bitfieldInfo.get(msg.hdr)))
            else:
                if fieldInfo.idbits == 0 and fieldInfo.name != u"DataLength" and fieldInfo.name != u"Time":
                    msg_route.append(unicode(fieldInfo.get(msg.hdr)))
        return msg_route

    class HeaderTranslator(object):
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
            
            HdrInfo = namedtuple(u'HdrInfo', u'type infoIndex timeField')
            self._hdr1Info = HdrInfo(hdr1, 0, Messaging.findFieldInfo(hdr1.fields, u"Time"))
            self._hdr2Info = HdrInfo(hdr2, 1, Messaging.findFieldInfo(hdr2.fields, u"Time"))

        def translateHdrAndBody(self, fromHdr, body):
            # figure out which direction to translate
            if isinstance(fromHdr, self._hdr1Info.type):
                fromHdrInfo = self._hdr1Info
                toHdrInfo = self._hdr2Info
            elif isinstance(fromHdr, self._hdr2Info.type):
                fromHdrInfo = self._hdr2Info
                toHdrInfo = self._hdr1Info
            else:
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
                    print u"message ID 0x" + hex(fromHdr.GetMessageID()) + u" translated to 0x" + hex(toHdr.GetMessageID()) + u", throwing away"
                return None
            # copy the body
            for i in xrange(0,fromHdr.GetDataLength()):
                toHdr.rawBuffer()[toHdr.SIZE+i] = body[i]
            
            # do special timestamp stuff to convert from relative to absolute time
            if toHdrInfo.timeField != None:
                if fromHdrInfo.timeField != None:
                    if fromHdrInfo.timeField.fieldSize < toHdrInfo.timeField.fieldSize:
                        # Detect time rolling
                        thisTimestamp = fromHdr.GetTime()
                        thisTime = datetime.now()
                        timestampOffset = self.timestampOffset
                        if thisTimestamp < self.lastTimestamp:
                            # If the timestamp shouldn't have wrapped yet, assume messages sent out-of-order,
                            # and do not wrap again.
                            if thisTime > self.lastWrapTime.addSecs(30):
                                self.lastWrapTime = thisTime
                                self.timestampOffset+=1
                                timestampOffset = self.timestampOffset
                        self.lastTimestamp = thisTimestamp
                        # need to handle different size timestamps!
                        toHdr.SetTime((timestampOffset << 16) + thisTimestamp)
                    else:
                        toHdr.SetTime(fromHdr.GetTime())
                else:
                    t = datetime.now().timestamp()
                    if float(toHdrInfo.timeField.maxVal) <= 2**32:
                        t = (datetime.fromtimestamp(t) - datetime.fromtimestamp(t).replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                    if toHdrInfo.timeField.units == u"ms":
                        t = t * 1000.0
                    if toHdrInfo.timeField.type == u"int":
                        t = int(t)
                    toHdr.SetTime(t)

            return toHdr

        def translate(self, fromHdr):
            toHdr = self.translateHdrAndBody(fromHdr, fromHdr.rawBuffer()[type(fromHdr).SIZE:])
            return toHdr

class BitFieldInfo(object):
    def __init__(self, name, type, units, minVal, maxVal, description, get, set, enum, idbits=0):
        self.name=name
        self.type=type
        self.units=units
        self.minVal=minVal
        self.maxVal=maxVal
        self.description=description
        self.get=get
        self.set=set
        self.enum=enum
        self.idbits=idbits

class FieldInfo(object):
    def __init__(self, name, type, units, minVal, maxVal, description, get, set, count, bitfieldInfo, enum, idbits=0):
        self.name=name
        self.type=type
        self.units=units
        self.minVal=minVal
        self.maxVal=maxVal
        self.description=description
        self.get=get
        self.set=set
        self.count=count
        self.bitfieldInfo=bitfieldInfo
        self.enum=enum
        self.idbits=idbits
