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

    def MsgAccessors(self, msg):
        # getmembers() gives a list of (name, value) tuples, and we want a list of values (function objects)
        #msgTupleList = inspect.getmembers(msg, lambda x: (inspect.ismethod(x) or inspect.isfunction(x) or inspect.ismethoddescriptor(x)) and "Get" in x.__name__)
        methods = inspect.getmembers(msg, predicate=inspect.ismethoddescriptor)
        methods = filter(lambda method: method[0].startswith('Get'), methods)
#        for i in methods:
#            print(str(i))
#            print("%s: %s" % (str(i[0]), str(i[1])))
        fns = list(x[1] for x in methods)
        fns.sort(key=Messaging.linenumber_of_member)
        fns = list(x.__func__ for x in fns)
        return fns

    # returns list of Set functions for fields of a message
    def MsgMutators(self, msg):
        # getmembers() gives a list of (name, value) tuples, and we want a list of values (function objects)
        msgTupleList = inspect.getmembers(msg, lambda x: inspect.isfunction(x) and "Set" in x.__name__)
        fns = list(x[1] for x in msgTupleList)
        fns.sort(key=Messaging.linenumber_of_member)
        return fns
