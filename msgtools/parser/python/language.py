import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

# >/</= means big/little/native endian, see docs for struct.pack_into or struct.unpack_from.
def fieldType(field):
    if MsgParser.big_endian:
        fieldTypeDict = \
        {"uint64":">Q", "uint32":">L", "uint16": ">H", "uint8": "B",
          "int64":">q",  "int32":">l",  "int16": ">h",  "int8": "b",
          "float64":">d", "float32":">f"}
    else:
        fieldTypeDict = \
        {"uint64":"<Q", "uint32":"<L", "uint16": "<H", "uint8": "B",
          "int64":"<q",  "int32":"<l",  "int16": "<h",  "int8": "b",
          "float64":"<d", "float32":"<f"}
    typeStr = field["Type"]
    return fieldTypeDict[typeStr]

def pythonFieldCount(field):
    count = MsgParser.fieldCount(field)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        count = 1
    return count

def reflectionInterfaceType(field):
    type = field["Type"]
    if "float" in type or fieldHasConversion(field):
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitsReflectionInterfaceType(field):
    type = "int"
    if fieldHasConversion(field):
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitfieldReflection(msg, field, bits):
    name = bits["Name"]
    ret = "BitFieldInfo("+\
              'name="'+name + '",'+\
              'type="'+bitsReflectionInterfaceType(bits) + '",'+\
              'units="'+MsgParser.fieldUnits(bits) + '",'+\
              'minVal="'+str(MsgParser.fieldMin(bits)) + '",'+\
              'maxVal="'+str(MsgParser.fieldMax(bits)) + '",'+\
              'description="'+MsgParser.fieldDescription(bits) + '",'+\
              'get='+"Get" + name + ','+\
              'set='+"Set" + name  + ', '
    if "IDBits" in bits:
        ret += "idbits="+str(bits["IDBits"])+","
    if "Enum" in bits:
        ret += "enum = ["+  bits["Enum"]+", " + "Reverse" + bits["Enum"]+"])"
    else:
        ret += "enum = [])"
    return ret

def fieldReflection(msg, field):
    fieldInfo = "FieldInfo("+\
                  'name="'+field["Name"] + '",'+\
                  'type="'+reflectionInterfaceType(field) + '",'+\
                  'units="'+MsgParser.fieldUnits(field) + '",'+\
                  'minVal="'+str(MsgParser.fieldMin(field)) + '",'+\
                  'maxVal="'+str(MsgParser.fieldMax(field)) + '",'+\
                  'description="'+MsgParser.fieldDescription(field) + '",'+\
                  'get='+"Get" + field["Name"] + ','+\
                  'set='+"Set" + field["Name"]  + ','+\
                  'count='+str(pythonFieldCount(field)) + ', '
    if "IDBits" in field:
        fieldInfo += "idbits="+str(field["IDBits"])+","
    if "Bitfields" in field:
        bitfieldInfo = []
        for bits in field["Bitfields"]:
            bitfieldInfo.append("    " + bitfieldReflection(msg, field, bits))
        fieldInfo += "bitfieldInfo = [\n" + ",\n".join(bitfieldInfo) + "], "
    else:
        fieldInfo += "bitfieldInfo = [], "
    if "Enum" in field:
        fieldInfo += "enum = [" + field["Enum"]+", " + "Reverse" + field["Enum"]+"])"
    else:
        fieldInfo += "enum = [])"
    return fieldInfo

def reflection(msg):
    fieldInfos = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInfos.append(fieldReflection(msg, field))
    return ",\n".join(fieldInfos)

# don't need separate field infos and reflection for python, just use reflection only, there's
# no need to worry about runtime overhead in doing so.
def fieldInfos(msg):
    pass

def fnHdr(field, offset, count, name):
    param = "self"
    if str.find(name, "Set") == 0:
        param += ", value"
    if  count > 1:
        param += ", idx"
    if str.find(name, "Set") != 0:
        if "Enum" in field:
            param += ", enumAsInt=False"
    if fieldHasConversion(field):
        param += ", convertFloat=True"
        
    min = MsgParser.fieldMin(field)
    max = MsgParser.fieldMax(field)
    
    try:
        fieldSize = MsgParser.fieldSize(field)
        if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
            count = MsgParser.fieldCount(field)
    except KeyError:
        fieldSize = 0
        
    ret = '''\
@msg.units('%s')
@msg.default('%s')
@msg.minVal('%s')
@msg.maxVal('%s')
@msg.offset('%s')
@msg.size('%s')
@msg.count(%s)
def %s(%s):
    """%s"""''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(min), str(max), str(offset), str(fieldSize), str(count), name, param, MsgParser.fieldDescription(field))
    return ret

def enumLookup(msg, field):
    lookup  = "defaultValue = 0\n"
    lookup += "    try:\n"
    lookup += "        value = int(float(value))\n"
    lookup += "    except ValueError:\n"
    lookup += "        pass\n"
    lookup += "    if isinstance(value, int) or value.isdigit():\n"
    lookup += "        defaultValue = int(value)\n"
    lookup += "    value = " + msgName(msg) + "." + str(field["Enum"]) + ".get(value, defaultValue)\n"
    lookup += "    "
    return lookup

def reverseEnumLookup(msg, field):
    lookup = "if not enumAsInt:\n"
    lookup += "        value = " + msgName(msg) + ".Reverse" + str(field["Enum"]) + ".get(value, value)\n    "
    return lookup

def getFn(msg, field):
    loc = msgName(msg) + ".MSG_OFFSET + " + str(MsgParser.fieldLocation(field))
    type = "'"+fieldType(field)+"'"
    count = MsgParser.fieldCount(field)
    cleanup = ""
    preface = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        cleanup = reverseEnumLookup(msg, field)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        preface += "\n    count = " + str(count)+"\n"
        preface += "    if count > len(self.rawBuffer())-("+loc+"):\n"
        preface += "        count = len(self.rawBuffer())-("+loc+")\n"
        type = "str(count)+'s'"
        count = 1
        cleanup = '''ascii_len = str(value).find("\\\\x00")
    value = str(value)[2:ascii_len]
    ''' 
    elif count > 1:
            loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
    if fieldHasConversion(field):
        cleanup = "if convertFloat:\n    "
        cleanup += "    value = " + MsgParser.getMath("value", field, "", conversionParamNames=True)+"\n    "
    ret = '''\
%s%s
    value = struct.unpack_from(%s, self.rawBuffer(), %s)[0]
    %sreturn value
''' % (fnHdr(field,MsgParser.fieldLocation(field),count, "Get"+field["Name"]), preface, type, loc, cleanup)
    return ret

def setFn(msg, field):
    loc = msgName(msg) + ".MSG_OFFSET + " + str(MsgParser.fieldLocation(field))
    count = MsgParser.fieldCount(field)
    type = fieldType(field)
    lookup = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        lookup = enumLookup(msg, field)
    if fieldHasConversion(field):
        lookup += "if convertFloat:\n    "
        lookup += "    value = %s\n    " % (MsgParser.setMath("value", field, "int", conversionParamNames=True))
    storageType = field["Type"]
    if "int" in storageType:
        lookup += "value = min(max(value, %s), %s)\n    " % (MsgParser.fieldStorageMin(storageType), MsgParser.fieldStorageMax(storageType))
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        type = str(count) + "s"
        count = 1
        lookup = "value = value.encode('utf-8')\n    "
    elif count > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
    ret  = '''\
%s
    %sstruct.pack_into('%s', self.rawBuffer(), %s, value)
''' % (fnHdr(field,MsgParser.fieldLocation(field),count, "Set"+field["Name"]), lookup, type, loc)
    return ret

def getBitsFn(msg, field, bits, bitOffset, numBits):
    cleanup = ""
    access = "(self.Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    if fieldHasConversion(bits):
        cleanup = "if convertFloat:\n    "
        cleanup += "    value = " + MsgParser.getMath("value", bits, "float", conversionParamNames=True)+"\n    "
    if "Enum" in bits:
        # find index that corresponds to string input param
        cleanup = reverseEnumLookup(msg, bits)
    ret  = '''\
%s
    value = %s
    %sreturn value
''' % (fnHdr(bits,MsgParser.fieldLocation(field),1,"Get"+MsgParser.BitfieldName(field, bits)), access, cleanup)
    return ret

def setBitsFn(msg, field, bits, bitOffset, numBits):
    lookup = ""
    if "Enum" in bits:
        # find index that corresponds to string input param
        lookup = enumLookup(msg, bits)
    if fieldHasConversion(bits):
        lookup += "if convertFloat:\n    "
        lookup += "    value = %s\n    " % (MsgParser.setMath("value", bits, "int", conversionParamNames=True))
    lookup += "value = min(max(value, %s), %s)\n    " % (0, str(2**numBits-1))
    ret = '''\
%s
    %sself.Set%s((self.Get%s() & ~(%s << %s)) | ((%s & %s) << %s))
''' % (fnHdr(bits,MsgParser.fieldLocation(field),1,"Set"+MsgParser.BitfieldName(field, bits)), lookup, field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), "value", MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            gets.append(getFn(msg, field))
            sets.append(setFn(msg, field))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    gets.append(getBitsFn(msg, field, bits, bitOffset, numBits))
                    sets.append(setBitsFn(msg, field, bits, bitOffset, numBits))
                    bitOffset += numBits

    return gets+sets

def initField(field, messageName):
    ret = []
    if "Default" in field:
        defaultValue = str(field["Default"])
        if pythonFieldCount(field) == 1:
            ret.append("self.Set" + field["Name"] + "(" + defaultValue + ")")
        else:
            ret.append("for i in range(0,"+str(pythonFieldCount(field))+"):")
            ret.append("    " + "self.Set" + field["Name"] + "(" + defaultValue + ", i)")
    return ret

def initBitfield(field, bits, messageName):
    ret = []
    if "Default" in bits:
        ret.append("self.Set" + MsgParser.BitfieldName(field, bits) + "(" + str(bits["Default"]) + ")")
    return ret

def initCode(msg):
    ret = []
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInit = initField(field, msgName(msg))
            if fieldInit:
                ret += fieldInit
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    bits = initBitfield(field, bits, msgName(msg))
                    if bits:
                        ret += bits

    return ret

def enums(e):
    ret = ""
    for enum in e:
        # forward enum
        fwd = enum["Name"]+" = OrderedDict(["
        for option in enum["Options"]:
            fwd += '("'+option["Name"]+'"'+", "+str(option["Value"]) + '), '
        fwd = fwd[:-2]
        fwd += "])\n"

        # Reverse enum
        back = "Reverse" + enum["Name"]+" = OrderedDict(["
        for option in enum["Options"]:
            back += "("+str(option["Value"]) +', "'+str(option["Name"]) + '"), '
        back = back[:-2]
        back += "])\n"

        ret += fwd + back
    return ret

def declarations(msg):
    return [""]

def getMsgID(msg):
    return baseGetMsgID("self.", "", 0, 1, msg)
    
def setMsgID(msg):
    return baseSetMsgID("self.", "", 0, 1, msg)

#
# MsgParser "event" handling functions
#
def onNewOutputDirectory(msgDir, outDir):
    '''Invoked by MsgParser when it's creating a new output directory.
    We need to create an empty __init__.py module in Python output
    directories so Python 2 can properly resolve modules.'''
    filename = os.path.join(outDir, '__init__.py')
    print('Creating %s' % filename)
    open(filename, 'at').close()