# for directory listing, exit function
import os, glob, sys, struct

# for reflection/introspection (find a class's methods)
import inspect

# for better 'import' functionality
import importlib

# for conversion to JSON
from collections import OrderedDict
import json

from collections import namedtuple
import ctypes
import time

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

class Messaging:
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

    def __init__(self, loadDir, debug, headerName):
        Messaging.debug = debug
        if not loadDir:
            srcdir=os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            loadDir = os.path.join(srcdir, "../../../obj/CodeGenerator/Python/")
            if not os.path.isdir(loadDir):
                srcdir = os.getcwd()
                loadDir = os.path.join(srcdir, "obj/CodeGenerator/Python/")
                while not os.path.isdir(loadDir):
                    lastsrcdir = srcdir
                    srcdir = os.path.abspath(os.path.join(srcdir, os.pardir))
                    # checking if joining with pardir returns the same dir is the easiest way to
                    # determine if we're at root of filesystem
                    if lastsrcdir == srcdir:
                        # if we're at root of filesystem, just give up!
                        loadDir = None
                        #print("\nERROR! Auto-generated python code not found!")
                        #print("cd to a directory downstream from a parent of obj/CodeGenerator/Python\n")
                        break
                    loadDir = srcdir + "/obj/CodeGenerator/Python/"
                    if Messaging.debug:
                        print("search for objdir in " + loadDir)
        sys.path.append(loadDir)
        sys.path.append(str(loadDir)+"/headers")
        
        # if we didn't find valid auto-generated code, this will cause an import error!
        # the fix is to point to valid auto-generated code!
        headerModule = __import__(headerName)

        # Set the global header name
        Messaging.hdr = getattr(headerModule, headerName)

        # specify our header size, to come from the generated header we imported
        Messaging.hdrSize = Messaging.hdr.SIZE

        self.LoadDir(loadDir)

    def LoadDir(self, loadDir):
        for filename in os.listdir(loadDir):
            filepath = loadDir + '/' + filename
            if os.path.isdir(filepath):
                if filename != 'headers':
                    if Messaging.debug:
                        print("descending into directory ", filepath)
                    self.LoadDir(filepath)
            elif filename.endswith('.py'):
                if Messaging.debug:
                    print("loading module "+filepath)
                name = filepath.replace("/", "_")
                importedModule = importlib.machinery.SourceFileLoader(name, filepath).load_module(name)

    # add message to the global hash table of names by ID, and IDs by name
    def Register(name, id, classDef):
        id = hex(id)
        
        if Messaging.debug:
            print("Registering", name, "as",id)
        
        if(id in Messaging.MsgNameFromID):
            print("WARNING! Trying to define message ", name, " for ID ", id, ", but ", Messaging.MsgNameFromID[id], " already uses that ID")
        
        Messaging.MsgNameFromID[id] = name

        if(name in Messaging.MsgIDFromName):
            print("WARNING! Trying to define message ", name, " for ID ", id, ", but ", Messaging.MsgIDFromName[name], " already uses that ID")
        Messaging.MsgIDFromName[name] = id

        if(name in Messaging.MsgClassFromName):
            print("WARNING! Trying to define message ", name, " but already in use by ID ", Messaging.MsgIDFromName[name])
        Messaging.MsgClassFromName[name] = classDef

        # split up the name between periods, and add it to the Messaging object so it
        # can be accessed via dot notation
        nameParts = name.split(".")
        messagingVars = vars(Messaging.Messages)
        for namePart in nameParts[:-1]:
            if namePart and not namePart in messagingVars:
                messagingVars[namePart] = lambda: None
            messagingVars = vars(messagingVars[namePart])
        messagingVars[nameParts[-1]] = classDef

    @staticmethod
    def MsgFactory(hdr):
        msgId = hex(hdr.GetMessageID())

        if not msgId in Messaging.MsgNameFromID:
            #print("WARNING! No definition for ", msgId, "!\n")
            from msgtools.lib.unknownmsg import UnknownMsg
            msgClass = UnknownMsg
        else:
            msgName = Messaging.MsgNameFromID[msgId]
            msgClass = Messaging.MsgClassFromName[msgName]
        
        msg = msgClass(hdr.rawBuffer())
        return msg

    @staticmethod
    def set(msg, fieldInfo, value, index=0):
        if("int" in fieldInfo.type):
            value = int(float(value))
        elif("float" in fieldInfo.type):
            value = float(value)
        
        if not hasattr(fieldInfo, "count") or fieldInfo.count == 1:
            fieldInfo.set(msg, value)
        else:
            fieldInfo.set(msg, value, index)

    @staticmethod
    def get(msg, fieldInfo, index=0):
        try:
            if not hasattr(fieldInfo, "count") or fieldInfo.count == 1:
                value = fieldInfo.get(msg)
            else:
                value = fieldInfo.get(msg, index)
        except struct.error:
            value = "UNALLOCATED"
        return str(value)

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
        msgClass = type(msg)
        pythonObj = OrderedDict()
        for fieldInfo in msgClass.fields:
            if(fieldInfo.count == 1):
                if len(fieldInfo.bitfieldInfo) == 0:
                    pythonObj[fieldInfo.name] = str(Messaging.get(msg, fieldInfo))
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        pythonObj[bitInfo.name] = str(Messaging.get(msg, bitInfo))
            else:
                arrayList = []
                for i in range(0,fieldInfo.count):
                    arrayList.append(str(Messaging.get(msg, fieldInfo, i)))
                pythonObj[fieldInfo.name] = arrayList

        return json.dumps({msg.MsgName() : pythonObj})

    @staticmethod
    def csvToMsg(lineOfText):
        if lineOfText == '':
            return None
        params = lineOfText.split()
        msgName = params[0]
        if len(params) == 1:
            params = []
        else:
            params = lineOfText.replace(msgName, "",1).split(',')
        if msgName in Messaging.MsgClassFromName:
            msgClass = Messaging.MsgClassFromName[msgName]
            msg = msgClass()
            if msg.fields:
                try:
                    paramNumber = 0
                    for fieldInfo in msgClass.fields:
                        if(fieldInfo.count == 1):
                            if len(fieldInfo.bitfieldInfo) == 0:
                                Messaging.set(msg, fieldInfo, params[paramNumber])
                                paramNumber+=1
                            else:
                                for bitInfo in fieldInfo.bitfieldInfo:
                                    Messaging.set(msg, bitInfo, params[paramNumber])
                                    paramNumber+=1
                        else:
                            arrayList = []
                            for i in range(0,fieldInfo.count):
                                Messaging.set(msg, fieldInfo, params[paramNumber], i)
                                paramNumber+=1
                except IndexError:
                    # if index error occurs on accessing params, then stop processing params
                    # because we've processed them all
                    pass
            return msg
        else:
            print("["+lineOfText+"] is NOT A MESSAGE NAME!")
        return None

    def long_substr(data):
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0])-i+1):
                    if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                        substr = data[0][i:i+j]
        return substr

    @staticmethod
    def csvHelp(lineOfText):
        autoComplete = None
        help = ""
        params = lineOfText.split()
        msgName = params[0]
        # if there's no params beyond first word, try to auto-complete a message name
        if len(params) == 1 and not lineOfText.endswith(" "):
            # search for messages that match us
            matchingMsgNames = []
            for aMsgName in sorted(Messaging.MsgClassFromName.keys()):
                if aMsgName.startswith(msgName):
                    matchingMsgNames.append(aMsgName)
            if len(matchingMsgNames) == 1:
                help = matchingMsgNames[0]
                autoComplete = matchingMsgNames[0]
                # if there's only one result and we don't match it exactly (because it's longer than us)
                # accept it by giving it as autoComplete with a space at end
                #if autoComplete != msgName:
                autoComplete = autoComplete + ' '
                return (autoComplete, help)
            else:
                help = '\n'.join(matchingMsgNames)
                autoComplete = Messaging.long_substr(matchingMsgNames)
                #print("long_substr returned " + autoComplete)
                return (autoComplete, help)
                

        # if we didn't auto-complete a message name above, then show help on params
        params = lineOfText.replace(msgName, "",1).split(',')
        if msgName in Messaging.MsgClassFromName:
            helpOnJustParam = False
            if not helpOnJustParam:
                help = msgName + " "
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
                                        return (None, fieldInfo.name)
                                    paramNumber+=1
                                else:
                                    help += fieldInfo.name + ", "
                            else:
                                for bitInfo in fieldInfo.bitfieldInfo:
                                    if helpOnJustParam:
                                        if paramNumber == len(params)-1:
                                            return (None, bitInfo.name)
                                        paramNumber+=1
                                    else:
                                        help += bitInfo.name + ", "
                        else:
                            if helpOnJustParam:
                                arrayList = []
                                for i in range(0,fieldInfo.count):
                                    if helpOnJustParam and paramNumber == len(params)-1:
                                        return (None, fieldInfo.name)
                                    paramNumber+=1
                            else:
                                help += fieldInfo.name + "["+str(fieldInfo.count)+"], "
                except IndexError:
                    # if index error occurs on accessing params, then stop processing params
                    # because we've processed them all
                    print("done at index " + str(paramNumber))
                    pass
                if help.endswith(", "):
                    help = help[:-2]
        else:
            return (None, "["+msgName+"] is not a message name!")
        return (autoComplete, help)

    # should this move to a member function of a hypothetical Message base class?
    @staticmethod
    def MsgRoute(msg):
        hdr = msg.hdr
        msg_route = []
        try:
            msg_route.append(str(hdr.GetSource()))
        except AttributeError:
            pass
        try:
            msg_route.append(str(hdr.GetDestination()))
        except AttributeError:
            pass
        try:
            msg_route.append(str(hdr.GetDeviceID()))
        except AttributeError:
            pass
        return msg_route

    class HeaderTranslator:
        startTime = int(time.time() * 1000)

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
                    print("message ID 0x" + hex(fromHdr.GetMessageID()) + " translated to 0x" + hex(toHdr.GetMessageID()) + ", throwing away")
                return None
            # copy the body
            for i in range(0,fromHdr.GetDataLength()):
                toHdr.rawBuffer()[toHdr.SIZE+i] = body[i]
            
            # do special timestamp stuff
            if toHdrInfo.timeField != None and fromHdrInfo.timeField != None and self.serialTimeFieldSize < self.networkTimeFieldSize:
                # Detect time rolling
                thisTimestamp = fromHdr.GetTime()
                thisTime = int(time.time() * 1000)
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
            elif toHdrInfo.timeField != None and fromHdrInfo.timeField == None:
                thisTime = int(time.time() * 1000)
                toHdr.SetTime(thisTime - self.startTime)

            return toHdr

        def translate(self, fromHdr):
            toHdr = self.translateHdrAndBody(fromHdr, fromHdr.rawBuffer()[type(fromHdr).SIZE:])
            return toHdr

class BitFieldInfo(object):
    def __init__(self, name, type, units, minVal, maxVal, description, get, set, enum):
        self.name=name
        self.type=type
        self.units=units
        self.minVal=minVal
        self.maxVal=maxVal
        self.description=description
        self.get=get
        self.set=set
        self.enum=enum

class FieldInfo(object):
    def __init__(self, name, type, units, minVal, maxVal, description, get, set, count, bitfieldInfo, enum):
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
