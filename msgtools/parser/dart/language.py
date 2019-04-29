import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def endian_string():
    if MsgParser.big_endian:
        return ''
    else:
        return ', Endian.little'

def fieldType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return typeStr.title()
    if typeStr == "float32":
        return "Float32";
    if typeStr == "float64":
        return "Float64";
    return "?"
    
def returnType(field, bits):
    typeStr = field["Type"]
    if "int" in typeStr:
        if "Offset" in field or "Scale" in field or (bits and ("Offset" in bits or "Scale" in bits)):
            return "double";
        return "int"
    elif typeStr == "float32" or typeStr == "float64":
        return "double";
    return "?"
    
def fnHdr(field):
    ret = "/* %s %s, (%s to %s)*/" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def getMath(x, field):
    ret = x
    if "Offset" in field or "Scale" in field:
        ret = "(%s).toDouble()" % (ret)
    if "Scale" in field:
        ret = "(%s * %s)" % (ret, fieldScale(field, ""))
    if "Offset" in field:
        ret = "(%s + %s)" % (ret, fieldOffset(field, ""))
    return ret

def setMath(x, field):
    ret = x
    if "Offset" in field:
        ret = "(%s - %s)" % (ret, fieldOffset(field, ""))
    if "Scale" in field:
        ret = "%s ~/ %s" % (ret, fieldScale(field, ""))
    if "Offset" in field or "Scale" in field:
        ret = "(%s).toInt()" % (ret)
    return ret


def getFn(field):
    loc = str(MsgParser.fieldLocation(field))
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += "int idx"
    access = "_data.get%s(%s%s)" % (fieldType(field), loc, endian_string())
    access = getMath(access, field)
    retType = returnType(field, None)
    #elif "Enum" in field:
    #    retType = field["Enum"]
    #    access = retType + "(" + access + ")"
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
    final StringBuffer ret = new StringBuffer();
    for(int i=0; i<%s && i<_hdr.GetDataLength()-%s; i++)
    {
        final String nextChar = new String.fromCharCode(Get%s(i));
        if(nextChar == '\\0')
            break;
        ret.write(nextChar);
    }
    return ret.toString();
}''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), str(MsgParser.fieldLocation(field)), field["Name"])
    return ret

def setFn(field):
    paramType = returnType(field, None)
    valueString = setMath("value", field)
    #if "Enum" in field:
    #    valueString = paramType + "(" + valueString + ")"
    #    paramType = field["Enum"]
    param = paramType + " value"
    loc = str(MsgParser.fieldLocation(field))
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += ", int idx"
    ret = '''\
%s
void Set%s(%s)
{
    _data.set%s(%s, %s%s);
}''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, valueString, endian_string())
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
void Set%sString(String value)
{
    for(int i=0; i<%s && i<value.length; i++)
    {
        Set%s(value.codeUnitAt(i), i);
    }
}''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), field["Name"])
    return ret

def getBitsFn(field, bits, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits)
    retType = returnType(field, bits)
    #if "Enum" in bits:
    #    retType = bits["Enum"]
    #    access = retType + "(" + access + ")"
    ret = '''\
%s
%s Get%s()
{
    return %s;
}''' % (fnHdr(bits), retType, MsgParser.BitfieldName(field, bits), access)
    return ret

def setBitsFn(field, bits, bitOffset, numBits):
    paramType = returnType(field, bits)
    valueString = setMath("value", bits)
    #if "Enum" in bits:
    #    valueString = paramType + "(" + valueString + ")"
    #    paramType = bits["Enum"]
    oldVal = '''%s() & ~(%s << %s)''' % ("Get"+field["Name"], MsgParser.Mask(numBits), str(bitOffset));
    newVal = '''(%s) | ((%s & %s) << %s)''' % (oldVal, valueString, MsgParser.Mask(numBits), str(bitOffset));
    ret = '''\
%s
void Set%s(%s value)
{
    %s(%s);
}''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), paramType, "Set"+field["Name"], newVal)
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            gets.append(getFn(field))
            sets.append(setFn(field))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    gets.append(getBitsFn(field, bits, bitOffset, numBits))
                    sets.append(setBitsFn(field, bits, bitOffset, numBits))
                    bitOffset += numBits

    return gets+sets

def fieldDefault(field):
    ret = field["Default"]
    return ret

def initField(field):
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for(int i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
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
        ret += "class <MSGNAME>_"+enum["Name"]+" {"
        for option in enum["Options"]:
            optionName = OptionName(option)
            ret += "static const int "+optionName+" = "+str(option["Value"]) + ';'
        ret += "}\n"
    return ret

def fieldReflectionType(field):
    ret = fieldType(field)
    if field["Type"] == "float32" or field["Type"] == "float64":
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
    if field["Type"] == "float32" or field["Type"] == "float64":
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

def fieldReflection(field):
    loc = str(MsgParser.fieldLocation(field))
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

def fieldBitsReflection(field, bits, bitOffset, numBits):
    loc = str(MsgParser.fieldLocation(field))
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
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(fieldReflection(field))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(fieldBitsReflection(field, bits, bitOffset, numBits))
                    bitOffset += numBits

    return "\n".join(ret)

def fieldMin(field):
    ret = str(MsgParser.fieldMin(field))
    if ret == 'DBL_MIN':
        ret = '-double.MAX_FINITE'
    elif ret == 'FLT_MIN':
        ret = '-3.402823466e38'
    return ret

def fieldMax(field):
    ret = str(MsgParser.fieldMax(field))
    if ret == 'DBL_MAX':
        ret = 'double.MAX_FINITE'
    elif ret == 'FLT_MAX':
        ret = '3.402823466e38'
    return ret

def genericInfo(field, fieldName, loc, fieldType):
    params  = 'static const int '+fieldName+'_Loc   = ' + loc + ';\n'
    params += 'static const '+fieldType+" "+fieldName+'_Max   = ' + fieldMax(field) + ';\n'
    params += 'static const '+fieldType+" "+fieldName+'_Min   = ' + fieldMin(field) + ';\n'
    params += 'static const String '+fieldName+"_Units = '" + str(MsgParser.fieldUnits(field)) + "'" + ';\n'
    params += 'static const int '+fieldName+'_Count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += 'static const '+fieldType+" "+fieldName+'_DefaultValue = ' + str(fieldDefault(field)) + ";\n" 
    if "Scale" in field:
        params += 'static const double '+fieldName+'_Scale = ' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += 'static const double '+fieldName+'_Offset = ' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field):
    params = genericInfo(field, field["Name"], str(MsgParser.fieldLocation(field)), returnType(field,None))
    return params

def fieldBitsInfo(field, bits, bitOffset, numBits):
    params  = genericInfo(bits, MsgParser.BitfieldName(field, bits), str(MsgParser.fieldLocation(field)), returnType(field,bits))
    params += 'static const int '+MsgParser.BitfieldName(field, bits)+'_BitOffset = ' + str(bitOffset) + ';\n'
    params += 'static const int '+MsgParser.BitfieldName(field, bits)+'_NumBits   = ' + str(numBits) + ';\n'
    return params

def fieldInfos(msg):
    ret = []
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(fieldInfo(field))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(fieldBitsInfo(field, bits, bitOffset, numBits))
                    bitOffset += numBits

    return "\n".join(ret)

def declarations(msg):
    return []

def getMsgID(msg):
    ret = baseGetMsgID("", "", 0, 0, msg)
    return ret.replace("uint32_t", "int")
    
def setMsgID(msg):
    return baseSetMsgID("", "", 0, 0, msg)
