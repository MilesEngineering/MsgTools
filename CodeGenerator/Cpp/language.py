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
    

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "int idx"
    ret = '''\
%s Get%s(%s)
{
    return *(%s*)&m_data[%s];
}
''' % (fieldType(field), field["Name"], param, fieldType(field), loc)
    return ret

def setFn(field, offset):
    param = fieldType(field) + "& value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", int idx"
    ret =  "void Set" + field["Name"] + "(" + param + ")\n"
    ret += "{\n"
    ret += "    *("+fieldType(field)+"*)&m_data["+loc+"] = value;\n"
    ret += "}\n"
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    ret =  fieldType(field) + " Get" + field["Name"] + bits["Name"] + "()\n"
    ret += "{\n"
    ret += "    return (Get"+field["Name"]+"() >> "+str(bitOffset)+") & "+MsgParser.Mask(numBits)+";\n"
    ret += "}\n"
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
#    ret =  "void Set" + field["Name"] + bits["Name"] + "(" + fieldType(field) + "& value)\n"
#    ret += "{\n"
#    ret += "    Set"+field["Name"]+"((Get"+field["Name"]+"() & ~("+MsgParser.Mask(numBits)+" << "+str(bitOffset)+")) | ((value & "+MsgParser.Mask(numBits)+") << "+str(bitOffset)+"));\n"
#    ret += "}\n"
    ret = '''\
void Set%s%s(%s& value)
{
    Set%s((Get%s() & ~(%s << %s)) | ((value & %s) << %s));
}
''' % (field["Name"], bits["Name"], fieldType(field), field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = ""
    sets = ""
    
    offset = 0
    for field in msg["Fields"]:
        gets += getFn(field, offset)
        sets += setFn(field, offset)
        bitOffset = 0
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                gets += getBitsFn(field, bits, offset, bitOffset, numBits)
                sets += setBitsFn(field, bits, offset, bitOffset, numBits)
                bitOffset += numBits
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return gets+sets
