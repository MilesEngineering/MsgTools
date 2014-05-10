import MsgParser

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

def getFn(field, offset):
    loc = str(offset)
    param = "bytes"
    type = fieldType(field)
    count = MsgParser.fieldCount(field)
    cleanup = ""
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
    ret = '''\
@staticmethod
@msg.units('%s')
@msg.defaultValue('%s')
@msg.count(%s)
def Get%s(%s):
    """%s"""
    value = struct.unpack_from('%s', bytes, %s)[0]
    %sreturn value
''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(count), field["Name"], param, MsgParser.fieldDescription(field), type, loc, cleanup)
    return ret

def setFn(field, offset):
    param = "bytes, value"
    loc = str(offset)
    count = MsgParser.fieldCount(field)
    type = fieldType(field)
    math = "tmp = value"
    if count > 1:
        if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
            type = str(count) + "s"
            count = 1
            math = "tmp = value.encode('utf-8')"
        else:
            loc += "+idx*" + str(MsgParser.fieldSize(field))
            param += ", idx"
    ret  = '''\
@staticmethod
@msg.units('%s')
@msg.defaultValue('%s')
@msg.count(%s)
def Set%s(%s):
    """%s"""
    %s
    struct.pack_into('%s', bytes, %s, tmp)
''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(count), field["Name"], param, MsgParser.fieldDescription(field), math, type, loc)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    ret  = '''\
@staticmethod
@msg.units('%s')
@msg.defaultValue('%s')
@msg.count(1)
def Get%s%s(bytes):
    """%s"""
    return (Get%s(bytes) >> %s) & %s
''' % (MsgParser.fieldUnits(bits), str(MsgParser.fieldDefault(field)), field["Name"], bits["Name"], MsgParser.fieldDescription(field), field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    ret = '''\
@staticmethod
@msg.units('%s')
@msg.defaultValue('%s')
@msg.count(1)
def Set%s%s(bytes, value):
    """%s"""
    Set%s(bytes, (Get%s(bytes) & ~(%s << %s)) | ((value & %s) << %s))
''' % (MsgParser.fieldUnits(bits), str(MsgParser.fieldDefault(bits)), field["Name"], bits["Name"], MsgParser.fieldDescription(field), field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 0
    for field in msg["Fields"]:
        gets.append(getFn(field, offset))
        sets.append(setFn(field, offset))
        bitOffset = 0
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                gets.append(getBitsFn(field, bits, offset, bitOffset, numBits))
                sets.append(setBitsFn(field, bits, offset, bitOffset, numBits))
                bitOffset += numBits
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return gets+sets

def initField(field):
    if "DefaultValue" in field:
        return  "Set" + field["Name"] + "(" + str(field["DefaultValue"]) + ")"
    return ""

def initBitfield(field, bits):
    if "DefaultValue" in bits:
        return  "Set" + field["Name"] + bits["Name"] + "(" +str(bits["DefaultValue"]) + ")"
    return ""

def initCode(msg):
    ret = []
    
    offset = 0
    for field in msg["Fields"]:
        fieldInit = initField(field)
        if fieldInit:
            ret.append(fieldInit)
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                bits = initBitfield(field, bits)
                if bits:
                    ret.append(bits)

    return ret

def enums(e):
    ret = ""
    for enum in e:
        ret +=  enum["Name"]+" = {"
        for option in enum["Options"]:
            ret += '"'+option["Name"]+'"'+" : "+str(option["Value"]) + ', '
        ret = ret[:-2]
        ret += "}\n"
    return ret
