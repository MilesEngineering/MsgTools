import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

# used as a prefix to namespace functions, enums, etc.
namespace = ""
enumClass = "class "
firstParam = ""
firstParamDecl = ""
const = " const"
enumNamespace = 0
functionPrefix = ""

def params(p1, p2):
    splitter = ""
    if p1 != "" and p2 != "":
        splitter = ", "
    return p1 + splitter + p2

def fieldType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return typeStr + "_t"
    if typeStr == "float32":
        return "float";
    if typeStr == "float64":
        return "double";
    return "?"
    
def fnHdr(field):
    ret = "/* %s %s, (%s to %s)*/" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def arrayAccessor(field):
    # if we've got floating point conversion, don't do an array accessor
    if "Offset" in field or "Scale" in field:
        return ""
    # if we're not an array, don't do an array accessor
    if MsgParser.fieldCount(field) == 1:
        return ""
    # if we're not contiguous, don't do an array accessor
    if MsgParser.fieldSize(field) != MsgParser.fieldArrayElementOffset(field):
        return ""
    # if we don't have natural alignment, don't do an array accessor
    if MsgParser.fieldLocation(field) % MsgParser.fieldSize(field) != 0:
        return ""
    loc = str(MsgParser.fieldLocation(field))
    access = "(%s*)&m_data[%s]" % (fieldType(field), loc)
    ret = '''\
%s
%s* %s(%s)
{
    return %s;
}''' % (fnHdr(field), functionPrefix+fieldType(field), namespace+field["Name"], firstParamDecl, access)

    if MsgParser.fieldSize(field) != 1:
        if MsgParser.big_endian:
            ret = "#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__ \n" + ret + "\n#endif\n"
        else:
            ret = "#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__ \n" + ret + "\n#endif\n"
    return ret

def castForScaledInt(field):
    ret = typeForScaledInt(field)
    if namespace != "":
        ret = "(" + ret + ")"
    return ret

def getFn(field):
    loc = str(MsgParser.fieldLocation(field))
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += "int idx"
    access = "Get_%s(&m_data[%s])" % (fieldType(field), loc)
    access = getMath(access, field, castForScaledInt(field), 'f')
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    elif "Enum" in field and namespace == "":
        retType = namespace+field["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s %s(%s)%s
{
    return %s;
}''' % (fnHdr(field), functionPrefix+retType, namespace+"Get"+field["Name"], params(firstParamDecl, param), const, access)
    if "float" in retType or "double" in retType:
        ret = "#ifndef DISABLE_FLOAT_ACCESSORS\n" + ret + "\n#endif\n"
    return ret

def setFn(field):
    paramType = fieldType(field)
    valueString = setMath("value", field, "("+fieldType(field)+")", 'f')
    if "Offset" in field or "Scale" in field:
        paramType = typeForScaledInt(field)
    elif "Enum" in field and namespace == "":
        valueString = "("+paramType+")" + "(" + valueString + ")"
        paramType = namespace+field["Enum"]
    param = paramType + " value"
    loc = str(MsgParser.fieldLocation(field))
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += ", int idx"
    ret = '''\
%s
%s %s(%s)
{
    Set_%s(&m_data[%s], %s);
}''' % (fnHdr(field), functionPrefix+"void", namespace+"Set"+field["Name"], params(firstParamDecl, param), fieldType(field), loc, valueString)
    if "float" in paramType or "double" in paramType:
        ret = "#ifndef DISABLE_FLOAT_ACCESSORS\n" + ret + "\n#endif\n"
    return ret

def getBitsFn(field, bits, bitOffset, numBits):
    access = "(%sGet%s(%s) >> %s) & %s" % (namespace, field["Name"], firstParam, str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, castForScaledInt(bits), 'f')
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)
    elif "Enum" in bits and namespace == "":
        retType = namespace+bits["Enum"]
        access = retType + "(" + access + ")"
    ret = '''\
%s
%s %s(%s)%s
{
    return %s;
}''' % (fnHdr(bits), functionPrefix+retType, namespace+"Get"+MsgParser.BitfieldName(field, bits), firstParamDecl, const, access)
    if "float" in retType or "double" in retType:
        ret = "#ifndef DISABLE_FLOAT_ACCESSORS\n" + ret + "\n#endif\n"
    return ret

def setBitsFn(field, bits, bitOffset, numBits):
    paramType = fieldType(field)
    valueString = setMath("value", bits, "("+fieldType(field)+")", 'f')
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    elif "Enum" in bits and namespace == "":
        valueString = "("+paramType+")" + "(" + valueString + ")"
        paramType = namespace+bits["Enum"]
    oldVal = '''%s(%s) & ~(%s << %s)''' % (namespace+"Get"+field["Name"], firstParam, MsgParser.Mask(numBits), str(bitOffset));
    newVal = '''(%s) | ((%s & %s) << %s)''' % (oldVal, valueString, MsgParser.Mask(numBits), str(bitOffset));
    ret = '''\
%s
%s %s(%s value)
{
    %s(%s);
}''' % (fnHdr(bits), functionPrefix+"void", namespace+"Set"+MsgParser.BitfieldName(field, bits), params(firstParamDecl, paramType), namespace+"Set"+field["Name"], params(firstParam, newVal))
    if "float" in paramType or "double" in paramType:
        ret = "#ifndef DISABLE_FLOAT_ACCESSORS\n" + ret + "\n#endif\n"
    return ret

def accessors(msg):
    gets = []
    sets = []
    arrayAccessors = []
    
    if "Fields" in msg:
        for field in msg["Fields"]:
            gets.append(getFn(field))
            sets.append(setFn(field))
            arrAcc = arrayAccessor(field)
            if arrAcc != "":
                arrayAccessors.append(arrAcc)
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    gets.append(getBitsFn(field, bits, bitOffset, numBits))
                    sets.append(setBitsFn(field, bits, bitOffset, numBits))
                    bitOffset += numBits

    return gets+sets+arrayAccessors

def fieldDefault(field, as_enum=False):
    ret = field["Default"]
    if("Type" in field and "int" in field["Type"]) and ret > 2**31:
        ret = str(ret)+'u'
    if as_enum and "Enum" in field:
        retType = "<MSGNAME>Message::"+field["Enum"]
        ret = "%s(%s)" % (retType, ret)
    return ret

def initField(field):
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for (int i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "    "+namespace+"Set" + field["Name"] + "(" + params(firstParam, str(fieldDefault(field, True))) + ", i);" 
            return ret;
        else:
            return  namespace+"Set" + field["Name"] + "(" + params(firstParam, str(fieldDefault(field, True))) + ");"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  namespace+"Set" + MsgParser.BitfieldName(field, bits) + "(" + params(firstParam,str(bits["Default"])) + ");"
    return ""

def initCode(msg):
    ret = []
    noInitCode = True
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
        ret +=  "enum " + enumClass + namespace + enum["Name"]+" {"
        for option in enum["Options"]:
            optionName = OptionName(option)
            if enumNamespace != 0:
                optionName = "<MSGNAME>"+"_"+enum["Name"] + "_" + optionName
            ret += optionName+" = "+str(option["Value"]) + ', '
        ret = ret[:-2]
        ret += "};\n"
    return ret

def fieldReflectionType(field):
    ret = fieldType(field)
    if ret == "double" or ret == "float":
        return "FloatFieldInfo"

    if ret.startswith("int"):
        ret = "IntFieldInfo"
    if ret.startswith("uint"):
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
    if ret == "double" or ret == "float":
        return "FloatFieldInfo"

    if ret.startswith("int"):
        ret = "IntFieldInfo"
    if ret.startswith("uint"):
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
    if "Scale" in field or "Offset" in field:
        ret += 'f'
    else:
        if fieldIsInt(field) and not fieldIsSigned(field):
            ret += 'U'
    return ret

def fieldMax(field):
    ret = str(MsgParser.fieldMax(field))
    if "Scale" in field or "Offset" in field:
        ret += 'f'
    else:
        if fieldIsInt(field) and not fieldIsSigned(field):
            ret += 'U'
    return ret

def genericInfo(field, loc, type):
    params  = '    int static constexpr loc   = ' + loc + ';\n'
    params += '    '+type+' static constexpr max   = ' + fieldMax(field) + ';\n'
    params += '    '+type+' static constexpr min   = ' + fieldMin(field) + ';\n'
    params += '    char static constexpr units[] = "' + str(MsgParser.fieldUnits(field)) + '"' + ';\n'
    params += '    int static constexpr count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += '    '+type+' static constexpr defaultValue = ' + str(fieldDefault(field)) + ";\n" 
    if "Scale" in field:
        params += '    auto static constexpr scale = ' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += '    auto static constexpr offset = ' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'struct ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, str(MsgParser.fieldLocation(field)), retType)
    params += '};\n'
    return params

def fieldBitsInfo(field, bits, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'struct ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, str(MsgParser.fieldLocation(field)), retType)
    params += '    auto static constexpr bitOffset = ' + str(bitOffset) + ';\n'
    params += '    auto static constexpr numBits   = ' + str(numBits) + ';\n'
    params += '};\n'
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

def getMsgID(msg):
    return baseGetMsgID("", "", "CAST_ENUMS", 0, msg)
    
def setMsgID(msg):
    return baseSetMsgID("", "", 1, 0, msg)
