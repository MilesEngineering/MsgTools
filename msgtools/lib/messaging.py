# for directory listing, exit function
import os, glob, sys, struct

# for reflection/introspection (find a class's methods)
import inspect

# for runtime module importing
import importlib

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

    @staticmethod
    def DetermineLoadDir(loaddir, searchdir):
        if loaddir:
            loadDir = loaddir
            pass
        else:
            if not searchdir or not os.path.isdir(searchdir):
                searchdir = os.getcwd()
            loadDir = os.path.join(searchdir, "obj/CodeGenerator/Python/")
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
                loadDir = searchdir + "/obj/CodeGenerator/Python/"
                if Messaging.debug:
                    print("search for objdir in " + loadDir)

        # Normalize our load directory path, and load message modules on the path and
        # fix the sys path for future imports
        loadDir = os.path.normpath(loadDir)
        
        # add these to the system path, to allow application code to import header and message files directly.
        sys.path.append(loadDir)
        sys.path.append(os.path.join(loadDir, "headers"))
        
        return loadDir


    @staticmethod
    def LoadHeader(loaddir=None, searchdir=None, headerName="NetworkHeader"):
        loadDir = Messaging.DetermineLoadDir(loaddir, searchdir)

    @staticmethod
    def LoadAllMessages(loaddir=None, searchdir=None, headerName="NetworkHeader"):
        '''
        This dynamically loads all generated message code, with each message registering itself
        with the Messaging class on import.  This allows us to support a number of utility
        functions for message creation, introspection, class lookup, etc

        loaddir - If set we use this as the base directory for generated message code.  Overrides searchdir.
        searchdir - If set we start a search for 'obj/CodeGenerator/Python' from searchdir, and moving up 
            to each parent directory until we find this folder.  If loaddir and searchdir are not set
            we default to the current directory.
        debug - print debugging information to the console.
        headerName - the default header to use when processing messages.  We assume this module resides
            in a 'headers' folder below our base message root directory.
        '''
        loadDir = Messaging.DetermineLoadDir(loaddir, searchdir)
        
        # if we didn't find valid auto-generated code, this will cause an import error!
        # the fix is to point to valid auto-generated code!
        headerModule = importlib.import_module("headers." + headerName)

        # Set the global header name
        Messaging.hdr = getattr(headerModule, headerName)

        # specify our header size, to come from the generated header we imported
        Messaging.hdrSize = Messaging.hdr.SIZE

        Messaging.LoadDir(loadDir, loadDir)

    @staticmethod
    def LoadDir(loadDir, rootDir):
        for filename in os.listdir(loadDir):
            filepath = loadDir + '/' + filename
            if os.path.isdir(filepath):
                if filename != 'headers':
                    if Messaging.debug:
                        print("descending into directory ", filepath)
                    Messaging.LoadDir(filepath, rootDir)
            elif filename.endswith('.py'):
                # Build an import friendly module name
                # Could've just passed the root length to be more efficient
                # but felt the easier readability was better than the miniscule
                # performance gain we could've had
                modulename = filepath[len(rootDir)+1:]
                modulename = modulename[0:modulename.rfind('.py')]
                modulename = modulename.replace(os.sep, '.')
                if Messaging.debug:
                    print("loading module "+modulename)

                importlib.import_module(modulename)

    @staticmethod
    def Register(name, id, classDef):
        'add message to the global hash table of names by ID, and IDs by name'

        id = hex(id)
        
        if Messaging.debug:
            print("Registering", name, "as",id)
        
        if(id in Messaging.MsgNameFromID):
            print("WARNING! Trying to define message ", name, " for ID ", id, ", but ", Messaging.MsgNameFromID[id], " already uses that ID")
        
        Messaging.MsgNameFromID[id] = name

        Messaging.AddAlias(name, id, classDef)

    @staticmethod
    def AddAlias(name, id, classDef):
        'add message to the global hash table of IDs by name'

        if(name in Messaging.MsgIDFromName):
            print("WARNING! Trying to define message %s for ID %s(%d), but %s(%d) already uses that name" % (name, id, int(id, 0), Messaging.MsgIDFromName[name], int(Messaging.MsgIDFromName[name], 0)))

        Messaging.MsgIDFromName[name] = id
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
    def MsgFactory(msg, name=None):
        '''Create a new message instance from the given msg

            msg - the header and message payload (as a NetworkHeader)

            name - will override msg - create an empty message by name

            return an instance of the message class for this msg, or UnknownMsg
                if we can't find this message type
        '''
        # TODO: We could do a type check here and support a NetworkHeader or
        # simple raw buffer
        if name is None:
            msgClass = Messaging.MsgClass(msg)
            return msgClass(msg.rawBuffer())

        if name not in Messaging.MsgClassFromName:
            return None

        return Messaging.MsgClassFromName[name]()

    @staticmethod
    def MsgClass(hdr):
        '''Find the message class for this message header

        hdr - the header for this message.  Need not be the full
            message, i.e. header + payload.

        return UnknownMsg if we can't find this message, otherwise
            a class reference to the message for the given header (by ID)
        '''
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
        if("int" in fieldInfo.type):
            if isinstance(value, str):
                value = value.strip()
                if value.startswith("0x"):
                    value = int(value, 0)
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
    def MsgRoute(msg):
        hdr = msg.hdr
        msg_route = []
        for fieldInfo in msg.hdr.fields:
            if fieldInfo.bitfieldInfo:
                for bitfieldInfo in fieldInfo.bitfieldInfo:
                    if bitfieldInfo.idbits == 0 and bitfieldInfo.name != "DataLength" and bitfieldInfo.name != "Time":
                        msg_route.append(str(bitfieldInfo.get(msg.hdr)))
            else:
                if fieldInfo.idbits == 0 and fieldInfo.name != "DataLength" and fieldInfo.name != "Time":
                    msg_route.append(str(fieldInfo.get(msg.hdr)))
        return msg_route

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
