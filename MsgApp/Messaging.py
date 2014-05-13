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
        mainObjDir = os.path.dirname(os.path.abspath(__file__)) + "/../CodeGenerator/obj/Python"
        sys.path.append(mainObjDir)
        headerName = "Network"
        headerModule = __import__(headerName)

        # Set the global header name
        Messaging.hdr = headerModule.NetworkHeader
        # add 32 for routing information
        Messaging.hdrSize = Messaging.hdr.SIZE
        
        for filename in glob.glob( os.path.join(loadDir, '*.py') ):
            if filename != (loadDir+"/"+headerName+".py"):
                moduleName = os.path.splitext(os.path.basename(filename))[0]
                if debug:
                    print("loading module ", filename, "as",moduleName)
                vars(self)[moduleName] = imp.load_source(moduleName,filename)
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
    def linenumber_of_member(m):
        try:
            return m.func_code.co_firstlineno
        except AttributeError:
            return -1
    def MsgFns(self, msg, name):
        # getmembers() gives a list of (name, value) tuples, and we want a list of values (function objects)
        methods = inspect.getmembers(msg, predicate=lambda x: inspect.ismethoddescriptor(x) or inspect.isfunction(x))
        methods = list(filter(lambda method: method[0].startswith(name), methods))
        fns = [x[1] for x in methods]
        fns.sort(key=Messaging.linenumber_of_member)
        for fn in fns:
            try:
                fn = x.__func__
            except:
                pass
        return fns

    def MsgAccessors(self, msg):
        return self.MsgFns(msg, "Get")

    def MsgMutators(self, msg):
        return self.MsgFns(msg, "Set")
