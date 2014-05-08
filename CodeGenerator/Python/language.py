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
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "idx"
    ret = '''\
\@staticmethod
\@msg.units('%s')
\@msg.defaultValue('%s')
\@msg.count(%s)
def Get%s(%s):
    value = struct.unpack_from('%s', bytes, %s)[0]
    return value
''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(MsgParser.fieldCount(field)), field["Name"], param, fieldType(field), loc)
    return ret

def setFn(field, offset):
    param = "value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", idx"
    ret  = '''\
\@staticmethod
\@msg.units('%s')
\@msg.defaultValue('%s')
\@msg.count(%s)
def Set%s(%s):
    tmp = value
    struct.pack_into('%s', bytes, %s, tmp)
''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(MsgParser.fieldCount(field)), field["Name"], param, fieldType(field), loc)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    ret  = '''\
\@staticmethod
\@msg.units('%s')
\@msg.defaultValue('%s')
\@msg.count(1)
def Get%s%s():
    return (Get%s() >> %s) & %s
''' % (MsgParser.fieldUnits(bits), str(MsgParser.fieldDefault(field)), field["Name"], bits["Name"], field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    ret = '''\
\@staticmethod
\@msg.units('%s')
\@msg.defaultValue('%s')
\@msg.count(1)
def Set%s%s(value):
    Set%s((Get%s() & ~(%s << %s)) | ((value & %s) << %s));
''' % (MsgParser.fieldUnits(bits), str(MsgParser.fieldDefault(bits)), field["Name"], bits["Name"], field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), MsgParser.Mask(numBits), str(bitOffset))
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
        return  "Set" + field["Name"] + "(" + str(field["DefaultValue"]) + ");"
    return ""

def initBitfield(field, bits):
    if "DefaultValue" in bits:
        return  "Set" + field["Name"] + bits["Name"] + "(" +str(bits["DefaultValue"]) + ");"
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
