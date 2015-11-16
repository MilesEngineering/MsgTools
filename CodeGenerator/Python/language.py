import MsgParser

# >/</= means big/little/native endian, see docs for struct.pack_into or struct.unpack_from.
def fieldType(field):
    fieldTypeDict = \
    {"uint64":">Q", "uint32":">L", "uint16": ">H", "uint8": "B",
      "int64":">q",  "int32":">l",  "int16": ">h",  "int8": "b",
      "float64":">d", "float32":">f"}
    typeStr = str.lower(field["Type"])
    return fieldTypeDict[typeStr]

def msgSize(msg):
    offset = 0
    for field in msg["Fields"]:
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)
    return offset

def pythonFieldCount(field):
    count = MsgParser.fieldCount(field)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        count = 1
    return count

def reflectionInterfaceType(field):
    type = field["Type"]
    if "float" in type or "Offset" in field or "Scale" in field:
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
    if "Offset" in field or "Scale" in field:
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
              'description="'+MsgParser.fieldDescription(bits) + '",'+\
              'get='+"Get" + name + ','+\
              'set='+"Set" + name  + ', '
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
                  'description="'+MsgParser.fieldDescription(field) + '",'+\
                  'get='+"Get" + field["Name"] + ','+\
                  'set='+"Set" + field["Name"]  + ','+\
                  'count='+str(pythonFieldCount(field)) + ', '
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
    for field in msg["Fields"]:
        fieldInfos.append(fieldReflection(msg, field))
    return ",\n".join(fieldInfos)

# don't need separate field infos and reflection for python, just use reflection only, there's
# no need to worry about runtime overhead in doing so.
def fieldInfos(msg):
    pass

def fnHdr(field, count, name):
    param = "message_buffer"
    if str.find(name, "Set") == 0:
        param += ", value"
    if  count > 1:
        param += ", idx"
    ret = '''\
@staticmethod
@msg.units('%s')
@msg.default('%s')
@msg.count(%s)
def %s(%s):
    """%s"""''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(count), name, param, MsgParser.fieldDescription(field))
    return ret

def enumLookup(msg, field):
    lookup  = "defaultValue = 0\n"
    lookup += "    if isinstance(value, int) or value.isdigit():\n"
    lookup += "        defaultValue = int(value)\n"
    lookup += "    value = " + msg["Name"] + "." + str(field["Enum"]) + ".get(value, defaultValue)\n"
    lookup += "    "
    return lookup

def reverseEnumLookup(msg, field):
    lookup = "value = " + msg["Name"] + ".Reverse" + str(field["Enum"]) + ".get(value, value)\n    "
    return lookup

def getFn(msg, field, offset):
    loc = msg["Name"] + ".MSG_OFFSET + " + str(offset)
    param = "message_buffer"
    type = fieldType(field)
    count = MsgParser.fieldCount(field)
    cleanup = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        cleanup = reverseEnumLookup(msg, field)
    if  count > 1:
        if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
            type = str(count) + "s"
            count = 1
            cleanup = '''ascii_len = str(value).find("\\\\x00")
    value = str(value)[2:ascii_len]
    ''' 
        else:
            loc += "+idx*" + str(MsgParser.fieldSize(field))
            param += ", idx"
    if "Offset" in field or "Scale" in field:
        cleanup = "value = " + MsgParser.getMath("value", field, "")+"\n    "
    ret = '''\
%s
    value = struct.unpack_from('%s', message_buffer, %s)[0]
    %sreturn value
''' % (fnHdr(field,count, "Get"+field["Name"]), type, loc, cleanup)
    return ret

def setFn(msg, field, offset):
    param = "message_buffer, value"
    loc = msg["Name"] + ".MSG_OFFSET + " + str(offset)
    count = MsgParser.fieldCount(field)
    type = fieldType(field)
    lookup = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        lookup = enumLookup(msg, field)
    math = MsgParser.setMath("value", field, "int")
    storageType = field["Type"]
    if "int" in storageType and not "Enum" in field:
        math = "min(max(%s, %s), %s)" % (math, MsgParser.fieldStorageMin(storageType), MsgParser.fieldStorageMax(storageType))
    math = lookup + "tmp = " + math
    if count > 1:
        if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
            type = str(count) + "s"
            count = 1
            math = "tmp = value.encode('utf-8')"
        else:
            loc += "+idx*" + str(MsgParser.fieldSize(field))
            param += ", idx"
    ret  = '''\
%s
    %s
    struct.pack_into('%s', message_buffer, %s, tmp)
''' % (fnHdr(field,count, "Set"+field["Name"]), math, type, loc)
    return ret

def getBitsFn(msg, field, bits, offset, bitOffset, numBits):
    access = "("+msg["Name"]+".Get%s(message_buffer) >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = MsgParser.getMath(access, bits, "float")
    cleanup = ""
    if "Enum" in bits:
        # find index that corresponds to string input param
        cleanup = reverseEnumLookup(msg, bits)
    ret  = '''\
%s
    value = %s
    %sreturn value
''' % (fnHdr(bits,1,"Get"+MsgParser.BitfieldName(field, bits)), access, cleanup)
    return ret

def setBitsFn(msg, field, bits, offset, bitOffset, numBits):
    lookup = ""
    if "Enum" in bits:
        # find index that corresponds to string input param
        lookup = enumLookup(msg, bits)
    math = "min(max(%s, %s), %s)" % (MsgParser.setMath("value", bits, "int"), 0, str(2**numBits-1))
    math = lookup + "tmp = " + math
    ret = '''\
%s
    %s
    %s.Set%s(message_buffer, (%s.Get%s(message_buffer) & ~(%s << %s)) | ((%s & %s) << %s))
''' % (fnHdr(bits,1,"Set"+MsgParser.BitfieldName(field, bits)), math, msg["Name"], field["Name"], msg["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), "tmp", MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 0
    for field in msg["Fields"]:
        gets.append(getFn(msg, field, offset))
        sets.append(setFn(msg, field, offset))
        bitOffset = 0
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                gets.append(getBitsFn(msg, field, bits, offset, bitOffset, numBits))
                sets.append(setBitsFn(msg, field, bits, offset, bitOffset, numBits))
                bitOffset += numBits
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return gets+sets

def initField(field, messageName):
    ret = []
    if "Default" in field:
        defaultValue = str(field["Default"])
        if "Enum" in field:
            defaultValue = messageName + "." + str(field["Enum"]) + "['" +str(field["Default"]) + "']"
        else:
            if pythonFieldCount(field) == 1:
                ret.append(messageName + ".Set" + field["Name"] + "(message_buffer, " + defaultValue + ")")
            else:
                ret.append("for i in range(0,"+str(pythonFieldCount(field))+"):")
                ret.append("    " + messageName + ".Set" + field["Name"] + "(message_buffer, " + defaultValue + ", i)")
    return ret

def initBitfield(field, bits, messageName):
    ret = []
    if "Default" in bits:
        ret.append(messageName + ".Set" + MsgParser.BitfieldName(field, bits) + "(message_buffer, " + str(bits["Default"]) + ")")
    return ret

def initCode(msg):
    ret = []
    
    offset = 0
    for field in msg["Fields"]:
        fieldInit = initField(field, msg["Name"])
        if fieldInit:
            ret += fieldInit
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                bits = initBitfield(field, bits, msg["Name"])
                if bits:
                    ret += bits

    return ret

def enums(e):
    ret = ""
    for enum in e:
        # forward enum
        fwd = enum["Name"]+" = {"
        for option in enum["Options"]:
            fwd += '"'+option["Name"]+'"'+" : "+str(option["Value"]) + ', '
        fwd = fwd[:-2]
        fwd += "}\n"

        # Reverse enum
        back = "Reverse" + enum["Name"]+" = {"
        for option in enum["Options"]:
            back += str(option["Value"]) +' : "'+str(option["Name"]) + '", '
        back = back[:-2]
        back += "}\n"

        ret += fwd + back
    return ret

def declarations(msg):
    return [""]