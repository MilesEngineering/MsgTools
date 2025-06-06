# for directory listing, exit function
import os, glob, sys, struct, time, json

# for runtime module importing
import importlib

# for getting current time
import datetime

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

import collections

# This simulates a hash table, but with lazy loading, where a module isn't
# loaded until an attempt is made to use it.  Until then, only None is stored
# at each hash table location, so that keys() still returns the expected list.
class MessageNameLoader(collections.UserDict):
    def __init__(self,*arg,**kw):
        super(MessageNameLoader, self).__init__(*arg, **kw)

    def __getitem__(self, key):
        if key in self.data and self.data[key] != None:
            return self.data[key]

        if key in Messaging.MsgModuleFromName:
            importlib.import_module(Messaging.MsgModuleFromName[key])
        if not key in self.data:
            raise KeyError("Invalid Message name %s" % (key))
        return self.data[key]

# This simulates an object with attributes, but with lazy loading, where a module isn't
# loaded until an attempt is made to use it.
class MessageAttributeLoader(object):
    def __init__(self, basename):
        self.basename = basename
    
    def Find(self, msgname):
        return self.__getattr__(msgname)

    def __getattr__(self, key):
        if self.basename:
            msgname = self.basename+"."+key
        else:
            msgname = key

        if msgname in Messaging.MsgModuleFromName:
            importlib.import_module(Messaging.MsgModuleFromName[msgname])
        if key in vars(self):
            return getattr(self, key)
        raise Messaging.LoadError(self.basename, key)

class TimestampFixer:
    def __init__(self):
        self.last_rx_time = None
        self.last_rx_timestamp = None
        self.time_info = Messaging.findFieldInfo(Messaging.hdr.fields, "Time")
        TIME_SCALES = {"s": 1.0, "ms": 1000.0, "us": 1000000.0, "ns": 1e9}
        try:
            self.time_scale = TIME_SCALES[self.time_info.units]
        except KeyError:
            self.time_scale = None
    
    def restore_timestamp(self, hdr, original_timestamp):
        if original_timestamp != None:
            hdr.SetTime(original_timestamp)

    def fix_timestamp(self, hdr):
        # if there's no time field, don't do anything
        if not self.time_info:
            return None

        if hdr.GetTime() == 0.0:
            original_timestamp = hdr.GetTime()
            # if time is zero, then check if we've previously had non-zero time
            if self.last_rx_time == None:
                # if we've never had time, then just use system time, but scaled
                current_time = datetime.datetime.now().timestamp()
                if self.time_scale != None:
                    current_time *= self.time_scale
                if self.time_info.type == "int":
                    current_time = int(current_time)
                hdr.SetTime(current_time)
            else:
                # if we have had time, then try scaling between wallclock time and message time.
                # If we can scale between wallclock time and message time, compute
                # a new time based on last rx time and elapsed time.
                if self.time_scale != None:
                    current_time = datetime.datetime.now().timestamp()
                    elapsed_time = current_time - self.last_rx_time
                    elapsed_time *= self.time_scale
                    if self.time_info.type == "int":
                        elapsed_time = int(elapsed_time)
                    new_time = self.last_rx_timestamp + elapsed_time
                    hdr.SetTime(new_time)
                else:
                    # otherwise, set time to timestamp of last reception
                    hdr.SetTime(self.last_rx_timestamp)
            return original_timestamp
        else:
            # If there's a valid timestamp record it to use the next time
            # a message comes in if it has no timestamp.
            self.last_rx_time = datetime.datetime.now().timestamp()
            self.last_rx_timestamp = hdr.GetTime()
        return None

class Messaging:
    hdr=None
    hdrSize=0

    # hash tables for msg lookups
    MsgNameFromID = {}
    MsgIDFromName = {}
    MsgClassFromName = MessageNameLoader()
    MsgModuleFromName = {}

    # container for accessing message classes via attributes.
    Messages = MessageAttributeLoader("")
        
    debug=0
    objdir=None

    class LoadError(Exception):
        def __init__(self, basename, submsgname):
            if basename == "":
                fullname = "Messages"
            else:
                fullname = "Messages."+basename
            txt = "'%s' does not contain '%s.%s'" % (fullname, fullname, submsgname)
            super().__init__(txt)
            self.basename = basename
            self.submsgname = submsgname

        def __str__(self):
            error_text = super().__str__()
            suggestions = self.valid_submsgs()
            if suggestions:
                error_text += "\nSuggestions:"
                for suggestion in suggestions:
                    error_text += f"\n- {suggestion}"
            return error_text

        def valid_submsgs(self):
            ret = []
            basename = self.basename
            if basename == "":
                basename = "Messages"
            else:
                basename = "Messages."+basename
            for msgname in Messaging.MsgModuleFromName:
                fullname = "Messages."+msgname
                #print("fullname: %s" % (fullname))
                if fullname.startswith(basename):
                    if fullname.replace(basename, "").count(".") == 1:
                        ret.append(fullname)
            return ret

    @staticmethod
    def DetermineLoadDir(loaddir, searchdir):
        if loaddir:
            loadDir = loaddir
        else:
            if not searchdir or not os.path.isdir(searchdir):
                searchdir = os.getcwd()
            loadDir = os.path.join(searchdir, "obj/CodeGenerator/Python/")
            while not os.path.isdir(loadDir):
                lastsearchdir = searchdir
                searchdir = os.path.abspath(os.path.join(searchdir, os.pardir))
                # checking if joining with pardir returns the same dir is the easiest way to
                # determine if we're at root of filesystem, and our upward search has to stop.
                if lastsearchdir == searchdir:
                    # check for global path to generated code
                    if os.path.isdir("/opt/msgtools/obj/CodeGenerator/Python/"):
                        loadDir = "/opt/msgtools/obj/CodeGenerator/Python/"
                        break
                    else:
                        # if we're at root of filesystem, just give up!
                        loadDir = None
                        raise RuntimeError('''
ERROR! Auto-generated python code not found!
cd to a directory downstream from a parent of obj/CodeGenerator/Python
or specify that directory with --msgdir=PATH''')
                loadDir = searchdir + "/obj/CodeGenerator/Python/"
                if Messaging.debug:
                    print("search for objdir in " + loadDir)

        # Normalize our load directory path, and load message modules on the path and
        # fix the sys path for future imports
        loadDir = os.path.normpath(loadDir)
        
        # add these to the system path, to allow application code to import header and message files directly.
        sys.path.append(loadDir)
        sys.path.append(os.path.join(loadDir, "headers"))
        
        Messaging.objdir = os.path.abspath(os.path.join(loadDir,"../.."))

        return loadDir


    @staticmethod
    def LoadHeader(loaddir=None, searchdir=None, headerName="NetworkHeader"):
        loadDir = Messaging.DetermineLoadDir(loaddir, searchdir)

        # if we didn't find valid auto-generated code, this will cause an import error!
        # the fix is to point to valid auto-generated code!
        headerModule = importlib.import_module("headers." + headerName)

        # Set the global header class
        Messaging.hdr = getattr(headerModule, headerName)

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
        if Messaging.hdr != None:
            print("Messaging.LoadAllMessages() called more than once.")
            print("Returning immediately instead of re-executing it!")
            return

        loadDir = Messaging.DetermineLoadDir(loaddir, searchdir)
        
        # if we didn't find valid auto-generated code, this will cause an import error!
        # the fix is to point to valid auto-generated code!
        headerModule = importlib.import_module("headers." + headerName)

        # Set the global header class
        Messaging.hdr = getattr(headerModule, headerName)

        # specify our header size, to come from the generated header we imported
        Messaging.hdrSize = Messaging.hdr.SIZE
        
        cache_filename = os.path.join(loadDir, 'msglib_cache.json')
        try:
            with open(cache_filename, 'r') as fp:
                msglibinfo = json.load(fp)
                Messaging.MsgNameFromID     = msglibinfo["MsgNameFromID"]
                Messaging.MsgIDFromName     = msglibinfo["MsgIDFromName"]
                Messaging.MsgModuleFromName = msglibinfo["MsgModuleFromName"]
                for name in Messaging.MsgIDFromName:
                    # Initialize all class lookups to None, unless they are already set.
                    # This is a signal for MessageNameLoader to do a lookup, while
                    # still providing keys() for users to access.
                    if not name in Messaging.MsgClassFromName:
                        Messaging.MsgClassFromName[name] = None
                    
                    # the below is used to populate the hierarchy of dot-notation,
                    # *except* for the final class at the end (which will be done
                    # with lazy lookup)
                    
                    # split up the name between periods, and add it to the Messaging object so it
                    # can be accessed via dot notation
                    nameParts = name.split(".")
                    messagingVars = vars(Messaging.Messages)
                    basename = ""
                    for namePart in nameParts[:-1]:
                        if basename:
                            basename = basename + "." + namePart
                        else:
                            basename = namePart
                        if namePart and not namePart in messagingVars:
                            messagingVars[namePart] = MessageAttributeLoader(basename)
                        messagingVars = vars(messagingVars[namePart])
                
                # now that cache is built, check if we need to load/reload
                # any files because their python is newer than the cache
                cache_file_timestamp = os.path.getmtime(cache_filename)
        except FileNotFoundError:
            cache_file_timestamp = 0

        write_cache_file = Messaging.LoadDir(loadDir, loadDir, cache_file_timestamp=cache_file_timestamp)

        if write_cache_file:
            # store a cache message ID, name, and file data
            msglibinfo = {
                "MsgNameFromID":     Messaging.MsgNameFromID,
                "MsgIDFromName":     Messaging.MsgIDFromName,
                "MsgModuleFromName": Messaging.MsgModuleFromName
            }
            with open(cache_filename, 'w') as fp:
                json.dump(msglibinfo, fp)

    @staticmethod
    def LoadDir(loadDir, rootDir, cache_file_timestamp=0):
        loaded = False
        for filename in os.listdir(loadDir):
            filepath = loadDir + '/' + filename
            if os.path.isdir(filepath):
                if filename != 'headers':
                    if Messaging.debug:
                        print("descending into directory ", filepath)
                    loaded_subdir = Messaging.LoadDir(filepath, rootDir, cache_file_timestamp)
                    loaded = loaded or loaded_subdir
            elif filename.endswith('.py'):
                file_timestamp = os.path.getmtime(filepath)
                if file_timestamp > cache_file_timestamp:
                    if Messaging.debug and cache_file_timestamp != 0:
                        print("%s out of date (%f > %f), reloading" % (filename, file_timestamp, cache_file_timestamp))
                    # Build an import friendly module name
                    # Could've just passed the root length to be more efficient
                    # but felt the easier readability was better than the miniscule
                    # performance gain we could've had
                    modulename = filepath[len(rootDir)+1:]
                    modulename = modulename[0:modulename.rfind('.py')]
                    modulename = modulename.replace('/', '.')
                    if Messaging.debug:
                        print("loading module "+modulename)
        
                    loaded = True
                    importlib.import_module(modulename)
        return loaded

    @staticmethod
    def Register(name, id, classDef):
        'add message to the global hash table of names by ID, and IDs by name'

        hexid = hex(id)
        
        if Messaging.debug:
            print("Registering", name, "as",hexid)
        
        if(hexid in Messaging.MsgNameFromID and Messaging.MsgNameFromID[hexid] != name):
            print("WARNING! Trying to define message ", name, " for ID ", hexid, ", but ", Messaging.MsgNameFromID[hexid], " already uses that ID")
        
        Messaging.MsgNameFromID[hexid] = name

        Messaging.AddAlias(name, id, classDef)

    @staticmethod
    def AddAlias(name, id, classDef):
        'add message to the global hash table of IDs by name'
        
        hexid = hex(id)

        if(name in Messaging.MsgIDFromName and Messaging.MsgIDFromName[name] != hexid):
            print("WARNING! Trying to define message %s for ID %s(%d), but %s(%d) already uses that name" % (name, hexid, id, Messaging.MsgIDFromName[name], int(Messaging.MsgIDFromName[name], 0)))

        Messaging.MsgIDFromName[name] = hexid
        Messaging.MsgClassFromName[name] = classDef
        Messaging.MsgModuleFromName[name] = classDef.__module__

        # split up the name between periods, and add it to the Messaging object so it
        # can be accessed via dot notation
        nameParts = name.split(".")
        messagingVars = vars(Messaging.Messages)
        basename = ""
        for namePart in nameParts[:-1]:
            if basename:
                basename = basename + "." + namePart
            else:
                basename = namePart
            if namePart and not namePart in messagingVars:
                messagingVars[namePart] = MessageAttributeLoader(basename)
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
        if("int" in fieldInfo.type or "enumeration" == fieldInfo.type):
            if isinstance(value, str):
                value = value.strip()
                if value.startswith("0x"):
                    value = int(value, 0)
        if("int" in fieldInfo.type):
            value = int(float(value))
        elif("float" in fieldInfo.type):
            value = float(value)
        
        if fieldInfo.count == 1:
            fieldInfo.set(msg, value)
        else:
            fieldInfo.set(msg, value, index)

    @staticmethod
    def get(msg, fieldInfo, index=0):
        try:
            if fieldInfo.count == 1:
                value = fieldInfo.get(msg)
            else:
                value = fieldInfo.get(msg, index)
            if "hex" == fieldInfo.units.lower():
                digits = fieldInfo.size*2
                value = ("0x%0"+str(digits)+"X") % (value)
        except struct.error:
            value = "UNALLOCATED"
        return value

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
            if name == fi.name:
                return fi
            for bfi in fi.bitfieldInfo:
                if name == bfi.name:
                    return bfi
        return None
    
    # Create a fake field.  This is useful if we want to compute data based on an
    # existing message's fields that we want to plot or log.
    @staticmethod
    def createFakeField(msg_class, name, units="", minVal="", maxVal="", description="Fake field!", count=1):
        def getFn(self, index=0):
            if count == 1:
                return self.fake_fields[name]
            else:
                return self.fake_fields[name][index]
        getFn.units = units
        getFn.default = ''
        getFn.minVal = minVal
        getFn.maxVal = maxVal
        getFn.offset = 0
        getFn.size = 0
        getFn.count = count
        def setFn(self, value, index=0):
            if count == 1:
                self.fake_fields[name] = value
            else:
                if not name in self.fake_fields:
                    self.fake_fields[name] = []
                self.fake_fields[name][index] = value
        setFn.units = units
        setFn.default = ''
        setFn.minVal = minVal
        setFn.maxVal = maxVal
        setFn.offset = 0
        setFn.size = 0
        setFn.count = count
        new_fi = FieldInfo(name, type="", units=units, minVal=minVal, maxVal=maxVal, description=description, get=getFn, set=setFn, count=count, bitfieldInfo=[], enum=[])
        msg_class.fields.append(new_fi)

    # This is composed of all the header fields that are not length, time, and any ID fields.
    # In some systems where one PC talks to one device, there may not be *any* fields that
    # contribute to Route.  In other systems it could be a device ID on a CANbus, a source
    # or destination field, or an IP Address or MAC address.
    # The reason MsgRoute exists is to distinguish between traffic with the same ID, that
    # is to, from, for, between different entities, so they aren't assumed to be two messages
    # in one time sequence.  This is necessary for showing lists of data (like msginspector),
    # showing plots of data as a time series, or showing the latest value of all data (msgscope).
    # As a performance optimization, the first time this function is called for a specific type
    # of header, we make a list of route fields, and then every time we need to generate a Route,
    # we loop through those fields.
    @staticmethod
    def HeaderRoute(hdr):
        try:
            routeFields = type(hdr).s_routeFields
        except AttributeError:
            routeFields = []
            for fieldInfo in hdr.fields:
                if fieldInfo.bitfieldInfo:
                    for bitfieldInfo in fieldInfo.bitfieldInfo:
                        if Messaging.IsRouteField(bitfieldInfo):
                            routeFields.append(bitfieldInfo)
                else:
                    if Messaging.IsRouteField(fieldInfo):
                        routeFields.append(fieldInfo)
            type(hdr).s_routeFields = routeFields
        # list comprehension to build the message route based on each of the route fields.
        msg_route = [str(route_field_info.get(hdr)) for route_field_info in routeFields]
        return msg_route

    @staticmethod
    def MsgRoute(msg):
        return Messaging.HeaderRoute(msg.hdr)
    
    # this sets up a message's header based on the given route
    #TODO Need special logic for headers with source and destination, because they need to be
    #TODO swapped if the message is coming or going.
    @staticmethod
    def SetMsgRoute(msg, msg_route):
        hdr = msg.hdr
        i = 0
        for fieldInfo in msg.hdr.fields:
            if fieldInfo.bitfieldInfo:
                for bitfieldInfo in fieldInfo.bitfieldInfo:
                    if Messaging.IsRouteField(bitfieldInfo):
                        Messaging.set(msg.hdr, bitfieldInfo, msg_route[i])
            else:
                if Messaging.IsRouteField(fieldInfo):
                    Messaging.set(msg.hdr, fieldInfo, msg_route[i])

    # fields count as Route fields unless they are part of the ID,
    # have "length" in their name, or match Time or Priority.
    @staticmethod
    def IsRouteField(fieldInfo):
        if fieldInfo.idbits != 0:
            return False
        if "length" in fieldInfo.name.lower():
            return False
        if fieldInfo.name == "Time":
            return False
        if fieldInfo.name == "Priority":
            return False
        return True
        
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
        self.count=1
        self.enum=enum
        self.idbits=idbits
        # add a couple fields from decorators of the 'get' function
        self.offset = get.offset
        self.size = get.size

    def exists(self, msg, index=0):
        return self.parent.exists(msg, index)

    def end_location(self, index=0):
        return self.parent.end_location(index)

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
        # add a couple fields from decorators of the 'get' function
        self.offset = int(get.offset)
        self.size = int(get.size)
        # give our bitfields a reference to us
        for bfi in self.bitfieldInfo:
            bfi.parent = self
            # Set the count of the bitfield to our own count, so that bitfields
            # in arrays work properly.
            bfi.count = count

    def exists(self, msg, index=0):
        end_of_field = self.offset + self.size * (index+1)
        if msg.hdr.GetDataLength() >= end_of_field:
            return True
        return False
    
    def end_location(self, index=0):
        return self.offset + self.size * (index+1)
