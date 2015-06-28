# for directory listing, exit function
import os, glob, sys, struct

# for reflection/introspection (find a class's methods)
import inspect

# for better 'import' functionality
import imp

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

class Messaging:
    hdr=None
    hdrSize=0

    # hash tables for msg lookups
    MsgNameFromID = {}
    MsgIDFromName = {}
    MsgClassFromName = {}
    
    debug=0

    def __init__(self, loadDir, debug):
        Messaging.debug = debug
        sys.path.append(loadDir)
        mainObjDir = os.path.dirname(os.path.abspath(__file__)) + "/../obj/CodeGenerator/Python"
        sys.path.append(mainObjDir)
        
        headerName = "Network"
        headerModule = __import__(headerName)

        # Set the global header name
        Messaging.hdr = headerModule.NetworkHeader

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
                moduleName = os.path.splitext(os.path.basename(filename))[0]
                if Messaging.debug:
                    print("loading module ", filepath, "as",moduleName)
                vars(self)[moduleName] = imp.load_source(moduleName,filepath)
                #print("vars(self)[%s] is "% moduleName, vars(self))
                

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

    @staticmethod
    def set(msgClass, message_buffer, fieldInfo, value, index=0):
        if("int" in fieldInfo.type):
            value = int(float(value))
        elif("float" in fieldInfo.type):
            value = float(value)
        if(fieldInfo.count == 1):
            getattr(msgClass, fieldInfo.set)(message_buffer, value)
        else:
            getattr(msgClass, fieldInfo.set)(message_buffer, value, index)

    @staticmethod
    def get(msgClass, message_buffer, fieldInfo, index=0):
        if(fieldInfo.count == 1):
            value = getattr(msgClass, fieldInfo.get)(message_buffer)
        else:
            value = getattr(msgClass, fieldInfo.get)(message_buffer, index)
        return str(value)

class FieldInfo(object):
    def __init__(self, name, type, units, description, get, set, count):
        self.name=name
        self.type=type
        self.units=units
        self.description=description
        self.get=get
        self.set=set
        self.count=count
