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

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "int idx"
    ret = '''\
// %s %s
%s Get%s(%s)
{
    return *(%s*)&m_data[%s];
}''' % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), fieldType(field), field["Name"], param, fieldType(field), loc)
    return ret

def setFn(field, offset):
    param = fieldType(field) + "& value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", int idx"
    ret = '''\
// %s %s
void Set%s(%s)
{
    *(%s*)&m_data[%s] = value;
}''' % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), field["Name"], param, fieldType(field), loc)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    ret =  fieldType(field) + " Get" + field["Name"] + bits["Name"] + "()\n"
    ret += "{\n"
    ret += "    return (Get"+field["Name"]+"() >> "+str(bitOffset)+") & "+MsgParser.Mask(numBits)+";\n"
    ret += "}"
    ret = '''\
// %s %s
%s Get%s%s()
{
    return (Get%s() >> %s) & %s;
}''' % (MsgParser.fieldDescription(bits), MsgParser.fieldUnits(bits), fieldType(field), field["Name"], bits["Name"], field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    ret = '''\
// %s %s
void Set%s%s(%s& value)
{
    Set%s((Get%s() & ~(%s << %s)) | ((value & %s) << %s));
}''' % (MsgParser.fieldDescription(bits), MsgParser.fieldUnits(bits), field["Name"], bits["Name"], fieldType(field), field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), MsgParser.Mask(numBits), str(bitOffset))
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
