# for directory listing, exit function
import os, glob, sys, struct

# for reflection/introspection (find a class's methods)
import inspect

# for better 'import' functionality
import imp

# for conversion to JSON
from collections import OrderedDict
import json

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
    
    debug=0

    def __init__(self, loadDir, debug, headerName):
        Messaging.debug = debug
        sys.path.append(loadDir)
        mainObjDir = os.path.dirname(os.path.abspath(__file__)) + "/../../obj/CodeGenerator/Python"
        sys.path.append(mainObjDir)
        sys.path.append(mainObjDir+"/headers")
        
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
                dirname = loadDir.split("/")[-1]
                moduleName = os.path.splitext(os.path.basename(filename))[0]
                if Messaging.debug:
                    print("loading module "+filepath+" as "+dirname+"."+moduleName)
                if dirname and not dirname in vars(self):
                    vars(self)[dirname] = lambda: None
                vars(vars(self)[dirname])[moduleName] = imp.load_source(filepath.replace("/", "_"), filepath)
                #print("vars(self)[%s] is "% moduleName, vars(self))
                

    # add message to the global hash table of names by ID, and IDs by name
    def Register(name, id, classDef):
        id = hex(id)
        name = name.replace("_", ".")
        
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

    @staticmethod
    def MsgFactory(hdr):
        msgId = hex(hdr.GetMessageID())

        if not msgId in Messaging.MsgNameFromID:
            #print("WARNING! No definition for ", msgId, "!\n")
            from UnknownMsg import UnknownMsg
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
        firstWord = lineOfText.split()[0]
        if firstWord in Messaging.MsgClassFromName:
            msgClass = Messaging.MsgClassFromName[firstWord]
            msg = msgClass()
            if msg.fields:
                paramString = lineOfText.replace(firstWord, "",1)
                params = paramString.split(',')
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
