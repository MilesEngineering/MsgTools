import MsgParser
from MsgUtils import *

def fieldType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"long","uint16": "int",   "uint8": "short",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "char",
      "float64":"double", "float32":"float"}
    typeStr = str.lower(field["Type"])
    return fieldTypeDict[typeStr]

def fieldAccessorType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"int", "uint16": "short", "uint8": "char",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "char",
      "float64":"double", "float32":"float"}
    typeStr = str.lower(field["Type"])
    type = fieldTypeDict[typeStr]
    return type.capitalize()

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "float"

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "int idx"
    access = "(%s)m_data.get%s(%s)" % (fieldType(field), fieldAccessorType(field), loc)
    access = getMath(access, field, typeForScaledInt(field), 'f')
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    elif "Enum" in field:
        retType = field["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s Get%s(%s)
{
    return %s;
}''' % (fnHdr(field), retType, field["Name"], param, access)
    return ret

def setFn(field, offset):
    paramType = fieldType(field)
    valueString = setMath("value", field, fieldType(field), 'f')
    if "Offset" in field or "Scale" in field:
        paramType = typeForScaledInt(field)
    elif "Enum" in field:
        valueString = paramType + "(" + valueString + ")"
        paramType = field["Enum"]
    param = paramType + " value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", int idx"
    ret = '''\
%s
void Set%s(%s)
{
    m_data.put%s(%s, (%s)%s);
}''' % (fnHdr(field), field["Name"], param, fieldAccessorType(field), loc, fieldAccessorType(field).lower(), valueString)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, typeForScaledInt(bits), 'f')
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)
    elif "Enum" in bits:
        retType = bits["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s Get%s()
{
    return %s;
}''' % (fnHdr(bits), retType, MsgParser.BitfieldName(field, bits), access)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    paramType = fieldType(field)
    valueString = setMath("value", bits, fieldType(field), 'f')
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    elif "Enum" in bits:
        valueString = paramType + "(" + valueString + ")"
        paramType = bits["Enum"]
    ret = '''\
%s
void Set%s(%s value)
{
    Set%s((Get%s() & ~(%s << %s)) | ((%s & %s) << %s));
}''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), paramType, field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 0
    if "Fields" in msg:
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
        if MsgParser.fieldCount(field) > 1:
            ret = "for (int i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "    Set" + field["Name"] + "(" + str(field["Default"]) + ", i);" 
            return ret;
        else:
            return  "Set" + field["Name"] + "(" + str(field["Default"]) + ");"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  "Set" + MsgParser.BitfieldName(field, bits) + "(" +str(bits["Default"]) + ");"
    return ""

def initCode(msg):
    ret = []
    
    offset = 0
    if "Fields" in msg:
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
    params = "FieldInfo";
    params += "("
    params += '"'+field["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(field) + '"'
    params += ', "' + MsgParser.fieldUnits(field) + '"'
    params += ", " + str(MsgParser.fieldCount(field))
    params += ")"
    return params

def fieldBitsReflection(field, bits, offset, bitOffset, numBits):
    loc = str(offset)
    params = "FieldInfo";
    params += "("
    params += '"'+bits["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(bits) + '"'
    params += ', "' + MsgParser.fieldUnits(bits) + '"'
    params += ", " + str(MsgParser.fieldCount(bits))
    params += ")"
    return params

def reflection(msg):
    ret = []
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(fieldReflection(field, offset))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(fieldBitsReflection(field, bits, offset, bitOffset, numBits))
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return "\n".join(ret)

def fieldMin(field):
    val = MsgParser.fieldMin(field)
    ret = str(val)
    if "Scale" in field or "Offset" in field:
        ret += 'f'
    else:
        try:
            if val > fieldStorageMax("int32"):
                ret += 'L'
        except TypeError:
            pass
    return ret

def fieldMax(field):
    val = MsgParser.fieldMax(field)
    ret = str(val)
    if "Scale" in field or "Offset" in field:
        ret += 'f'
    else:
        try:
            if val > fieldStorageMax("int32"):
                ret += 'L'
        except TypeError:
            pass
    return ret

def genericInfo(field, type, offset):
    loc = str(offset)
    params  = '    static final int loc   = ' + loc + ';\n'
    params += '    static final '+type+' max   = ' + fieldMax(field) + ';\n'
    params += '    static final '+type+' min   = ' + fieldMin(field) + ';\n'
    params += '    static final String units = "' + str(MsgParser.fieldUnits(field)) + '"' + ';\n'
    params += '    static final int count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += '    static final '+type+' defaultValue = ' + str(field["Default"]) + ";\n" 
    if "Scale" in field:
        params += '    static final int scale = ' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += '    static final int offset = ' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field, offset):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'class ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, retType, offset)
    params += '};\n'
    return params

def fieldBitsInfo(field, bits, offset, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'class ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, retType, offset)
    params += '    static final int bitOffset = ' + str(bitOffset) + ';\n'
    params += '    static final int numBits   = ' + str(numBits) + ';\n'
    params += '};\n'
    return params

def fieldInfos(msg):
    ret = []
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(fieldInfo(field, offset))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(fieldBitsInfo(field, bits, offset, bitOffset, numBits))
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return "\n".join(ret)

def structUnpacking(msg):
    ret = []

    if "Fields" in msg:    
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append(bits["Name"] + " = msg.Get" + bits["Name"] + "();")
            else:
                if MsgParser.fieldCount(field) == 1:
                    ret.append(field["Name"] + " = msg.Get" + field["Name"] + "();")
                else:
                    ret.append("for(int i=0; i<"+str(MsgParser.fieldCount(field))+"; i++)")
                    ret.append("    "+field["Name"] + "[i] = msg.Get" + field["Name"] + "(i);")
            
    return "\n".join(ret)
    
def structPacking(msg):
    ret = []

    if "Fields" in msg:    
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append("msg.Set" + bits["Name"] + "("+bits["Name"]+");")
            else:
                if MsgParser.fieldCount(field) == 1:
                    ret.append("msg.Set" + field["Name"] + "("+field["Name"]+");")
                else:
                    ret.append("for(int i=0; i<"+str(MsgParser.fieldCount(field))+"; i++)")
                    ret.append("    msg.Set" + field["Name"] + "("+field["Name"] + "[i], i);")
                
    return "\n".join(ret)
    
def declarations(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    retType = fieldType(field)
                    if "Offset" in bits or "Scale" in bits:
                        retType = typeForScaledInt(bits)
                    elif "Enum" in bits:
                        retType = "<MSGNAME>Message::"+bits["Enum"]
                    ret.append(retType + " " + bits["Name"] + ";")
            else:
                retType = fieldType(field)
                if "Offset" in field or "Scale" in field:
                    retType = typeForScaledInt(field)
                elif "Enum" in field:
                    retType = "<MSGNAME>Message::"+field["Enum"]
                if MsgParser.fieldCount(field) == 1:
                    ret.append(retType + " " + field["Name"] + ";")
                else:
                    ret.append(retType + " " + field["Name"] + "["+str(MsgParser.fieldCount(field))+"];")
    return ret
