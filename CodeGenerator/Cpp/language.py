import MsgParser

def fieldType(field):
    typeStr = field["Type"]
    if str.find(typeStr, "int") != -1:
        return typeStr + "_t"
    if str.lower(typeStr) == "float32":
        return "float";
    if str.lower(typeStr) == "float64":
        return "double";
    return "?"
    
def msgSize(msg):
    offset = 0
    for field in msg["Fields"]:
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)
    return offset

def fnHdr(field):
    ret = "// %s %s" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field))
    return ret

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "int idx"
    access = "*(%s*)&m_data[%s]" % (fieldType(field), loc)
    access = MsgParser.getMath(access, field, "float")
    ret = '''\
%s
%s Get%s(%s)
{
    return %s;
}''' % (fnHdr(field), fieldType(field), field["Name"], param, access)
    return ret

def setFn(field, offset):
    param = fieldType(field) + " value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", int idx"
    ret = '''\
%s
void Set%s(%s)
{
    *(%s*)&m_data[%s] = %s;
}''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, MsgParser.setMath("value", field, fieldType(field)))
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = MsgParser.getMath(access, bits, "float")
    ret = '''\
%s
%s Get%s%s()
{
    return %s;
}''' % (fnHdr(bits), fieldType(field), field["Name"], bits["Name"], access)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    value = MsgParser.setMath("value", bits, fieldType(field))
    ret = '''\
%s
void Set%s%s(%s value)
{
    Set%s((Get%s() & ~(%s << %s)) | ((%s & %s) << %s));
}''' % (fnHdr(bits), field["Name"], bits["Name"], fieldType(field), field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), value, MsgParser.Mask(numBits), str(bitOffset))
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
    if "Default" in field:
        return  "Set" + field["Name"] + "(" + str(field["Default"]) + ");"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  "Set" + field["Name"] + bits["Name"] + "(" +str(bits["Default"]) + ");"
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
        ret +=  "enum " + enum["Name"]+" {"
        for option in enum["Options"]:
            ret += option["Name"]+" = "+str(option["Value"]) + ', '
        ret = ret[:-2]
        ret += "};\n"
    return ret

def fieldReflection(field, offset):
    loc = str(offset)
    type = fieldType(field)
    params = "{"
    params += '"'+field["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(field) + '"'
    params += ', "' + MsgParser.fieldUnits(field) + '"'
    params += ", " + loc
    params += ", " + str(MsgParser.fieldSize(field))
    params += ", " + str(MsgParser.fieldCount(field))
    if "Offset" in field or "Scale" in field:
        type = "ScaledFieldInfo"
        if "Scale" in field:
            params += ", " + field["Scale"]
        else:
            params += ", 1.0"
        if "Offset" in field:
            params = ", " + field["Offset"]
        else:
            params += ", 0.0"
    params += "}"
    return params

def reflection(msg):
    ret = []
    
    offset = 0
    for field in msg["Fields"]:
        ret.append(fieldReflection(field, offset))
        bitOffset = 0
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                ret.append(fieldBitsReflection(field, bits, offset, bitOffset, numBits))
                bitOffset += numBits
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return ret
