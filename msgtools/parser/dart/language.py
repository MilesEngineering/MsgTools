import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def fieldType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return typeStr.title()
    if str.lower(typeStr) == "float32":
        return "Float32";
    if str.lower(typeStr) == "float64":
        return "Float64";
    return "?"
    
def returnType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return "int"
    if str.lower(typeStr) == "float32" or str.lower(typeStr) == "float64":
        return "double";
    return "?"
    
def fnHdr(field):
    ret = "/* %s %s, (%s to %s)*/" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def castForScaledInt(field):
    return "double"

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "int idx"
    access = "_data.get%s(%s)" % (fieldType(field), loc)
    access = getMath(access, field, castForScaledInt(field), '')
    retType = returnType(field)
    if "Offset" in field or "Scale" in field:
        retType = "double"
    elif "Enum" in field:
        retType = field["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s Get%s(%s)
{
    return %s;
}''' % (fnHdr(field), retType, field["Name"], param, access)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
String Get%sString()
{
    String ret = "";
    for(int i=0; i<%s && i<_hdr.GetDataLength()-%s; i++)
    {
        nextChar = String.fromCharCode(Get%s(i));
        if(nextChar == '\\0')
            break;
        value += nextChar;
    }
    return ret;
}''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), offset, field["Name"])
    return ret

def setFn(field, offset):
    paramType = returnType(field)
    valueString = setMath("value", field, "int", '')
    if "Offset" in field or "Scale" in field:
        paramType = "double"
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
Set%s(%s)
{
    _data.set%s(%s, %s);
}''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, valueString)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
Set%sString(String value)
{
    for(int i=0; i<%s && i<value.length; i++)
    {
        Set%s(value.codeUnitAt(i), i);
    }
}''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), field["Name"])
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, castForScaledInt(bits), '')
    retType = returnType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = "double"
    elif "Enum" in bits:
        retType = bits["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s %s()
{
    return %s;
}''' % (fnHdr(bits), retType, "Get"+MsgParser.BitfieldName(field, bits), access)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    paramType = returnType(field)
    valueString = setMath("value", bits, "int", '')
    if "Offset" in bits or "Scale" in bits:
        paramType = "double"
    elif "Enum" in bits:
        valueString = paramType + "(" + valueString + ")"
        paramType = bits["Enum"]
    oldVal = '''%s() & ~(%s << %s)''' % ("Get"+field["Name"], MsgParser.Mask(numBits), str(bitOffset));
    newVal = '''(%s) | ((%s & %s) << %s)''' % (oldVal, valueString, MsgParser.Mask(numBits), str(bitOffset));
    ret = '''\
%s
%s(%s value)
{
    %s(%s);
}''' % (fnHdr(bits), "Set"+MsgParser.BitfieldName(field, bits), paramType, "Set"+field["Name"], newVal)
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

def fieldDefault(field):
    ret = field["Default"]
    return ret

def initField(field):
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for (int i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "    Set" + field["Name"] + "(" + str(fieldDefault(field)) + ", i);" 
            return ret;
        else:
            return  "Set" + field["Name"] + "(" + str(fieldDefault(field)) + ");"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  "Set" + MsgParser.BitfieldName(field, bits) + "(" + str(bits["Default"]) + ");"
    return ""

def initCode(msg):
    ret = []
    noInitCode = True
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInit = initField(field)
            if fieldInit:
                ret.append(fieldInit)
                noInitCode = False
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    bits = initBitfield(field, bits)
                    if bits:
                        ret.append(bits)
                        noInitCode = False
    if noInitCode:
        ret.append("UNUSED(m_data);")

    return ret

def enums(e):
    ret = ""
    for enum in e:
        ret += "class <MSGNAME>_"+enum["Name"]+" {"
        for option in enum["Options"]:
            optionName = OptionName(option)
            ret += "static const "+optionName+" = "+str(option["Value"]) + ';'
        ret += "}\n"
    return ret

def fieldReflectionType(field):
    ret = fieldType(field)
    if str.lower(field["Type"]) == "float32" or str.lower(field["Type"]) == "float64":
        return "FloatFieldInfo"

    if ret.lower().startswith("int"):
        ret = "IntFieldInfo"
    if ret.lower().startswith("uint"):
        ret = "UIntFieldInfo"

    if "NumBits" in field:
        ret = "BitfieldInfo"
        if "Offset" in field or "Scale" in field:
            ret = "ScaledBitfieldInfo"
    else:
        if "Offset" in field or "Scale" in field:
            ret = "ScaledFieldInfo"
    if "Enum" in field:
        ret = "EnumFieldInfo"
    return ret

def fieldReflectionBitsType(field, bits):
    ret = fieldType(field)
    if str.lower(field["Type"]) == "float32" or str.lower(field["Type"]) == "float64":
        return "FloatFieldInfo"

    if ret.lower().startswith("int"):
        ret = "IntFieldInfo"
    if ret.lower().startswith("uint"):
        ret = "UIntFieldInfo"

    if "NumBits" in bits:
        ret = "BitfieldInfo"
        if "Offset" in bits or "Scale" in bits:
            ret = "ScaledBitfieldInfo"
    else:
        if "Offset" in field or "Scale" in field:
            ret = "ScaledFieldInfo"
    if "Enum" in field:
        ret = "EnumFieldInfo"
    return ret

def fieldReflection(field, offset):
    loc = str(offset)
    type = fieldReflectionType(field)
    params = type;
    params += "("
    params += '"'+field["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(field) + '"'
    params += ', "' + MsgParser.fieldUnits(field) + '"'
    params += ", " + loc
    params += ", " + str(MsgParser.fieldSize(field))
    params += ", " + str(MsgParser.fieldCount(field))
    if "Offset" in field or "Scale" in field:
        if "Scale" in field:
            params += ", " + str(field["Scale"])
        else:
            params += ", 1.0"
        if "Offset" in field:
            params += ", " + str(field["Offset"])
        else:
            params += ", 0.0"
    params += ")"
    return params

def fieldBitsReflection(field, bits, offset, bitOffset, numBits):
    loc = str(offset)
    type = fieldReflectionBitsType(field, bits)
    params = type;
    params += "("
    params += '"'+bits["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(bits) + '"'
    params += ', "' + MsgParser.fieldUnits(bits) + '"'
    params += ", " + loc
    params += ", " + str(MsgParser.fieldSize(field))
    params += ", " + str(MsgParser.fieldCount(bits))
    if "Offset" in bits or "Scale" in bits:
        if "Scale" in bits:
            params += ", " + str(bits["Scale"])
        else:
            params += ", 1.0"
        if "Offset" in bits:
            params += ", " + str(bits["Offset"])
        else:
            params += ", 0.0"
    params += ", " + str(bitOffset)
    params += ", " + str(numBits)
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
    ret = str(MsgParser.fieldMin(field))
    return ret

def fieldMax(field):
    ret = str(MsgParser.fieldMax(field))
    return ret

def genericInfo(field, offset, fieldName):
    loc = str(offset)
    params  = 'static const '+fieldName+'_Loc   = ' + loc + ';\n'
    params += 'static const '+fieldName+'_Max   = ' + fieldMax(field) + ';\n'
    params += 'static const '+fieldName+'_Min   = ' + fieldMin(field) + ';\n'
    params += 'static const '+fieldName+'_Units = "' + str(MsgParser.fieldUnits(field)) + '"' + ';\n'
    params += 'static const '+fieldName+'_Count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += 'static const '+fieldName+'_DefaultValue = ' + str(fieldDefault(field)) + ";\n" 
    if "Scale" in field:
        params += 'static const '+fieldName+'_Scale = ' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += 'static const '+fieldName+'_Offset = ' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field, offset):
    params = genericInfo(field, offset, field["Name"])
    return params

def fieldBitsInfo(field, bits, offset, bitOffset, numBits):
    params  = genericInfo(bits, offset, MsgParser.BitfieldName(field, bits))
    params += 'static const '+MsgParser.BitfieldName(field, bits)+'_BitOffset = ' + str(bitOffset) + ';\n'
    params += 'static const '+MsgParser.BitfieldName(field, bits)+'_NumBits   = ' + str(numBits) + ';\n'
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

def declarations(msg):
    return []

def getMsgID(msg):
    return baseGetMsgID("", "", "CAST_ENUMS", 0, msg)
    
def setMsgID(msg):
    return baseSetMsgID("", "", 1, 0, msg)
