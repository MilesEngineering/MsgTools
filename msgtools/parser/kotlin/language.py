import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

oneOutputFilePerMsg = True

def endian_string():
    if MsgParser.big_endian:
        return ''
    else:
        return ', true'

def paramType(field):
    fieldTypeDict = \
    {"uint64":"Ulong", "uint32":"UInt","uint16": "UShort",   "uint8": "UByte",
     "int64":"Long",   "int32":"Int",  "int16": "Short",  "int8": "Byte",
      "float64":"Double", "float32":"Float"}
    typeStr = field["Type"]
    return fieldTypeDict[typeStr]

def fieldType(field):
    fieldTypeDict = \
    {"uint64":"Ulong", "uint32":"UInt","uint16": "UShort",   "uint8": "UByte",
     "int64":"Long",   "int32":"Int",  "int16": "Short",  "int8": "Byte",
      "float64":"Double", "float32":"Float"}
    typeStr = field["Type"]
    return fieldTypeDict[typeStr]

def bitParamType(field, bitfield):
    ret = paramType(field)
    if "Offset" in bitfield or "Scale" in bitfield:
        return typeForScaledInt(field)
    return ret

def isUnsigned(field):
    typeStr = field["Type"]
    if typeStr == "uint8" or typeStr == "uint16" or typeStr == "uint32":
        return True
    return False

def literalSuffix(field):
    typeStr = field["Type"]
    if  "Offset" in field or "Scale" in field:
        if typeForScaledInt(field) == "Float":
            return "f"
        return ""
    if typeStr == "float32":
        return "f"
    if typeStr == "uint8" or typeStr == "uint16" or typeStr == "uint32":
        return "u"
    return ""

def literalSuffixForBitfield(field, bits):
    typeStr = field["Type"]
    if  "Offset" in field or "Scale" in bits:
        if typeForScaledInt(field) == "Float":
            return "f"
    return literalSuffix(field)


def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = fieldNumBits(field)
    if numBits > 24:
        return "Double"
    return "Float"

# for floats, append tag such as 'f' to constants to eliminate compiler warnings
def fieldScale(field):
    if "Scale" in field:
        ret = field["Scale"]
        if typeForScaledInt(field) == "Float":
            ret = str(ret) + "f"
    return ret

def fieldOffset(field):
    if "Offset" in field:
        ret = field["Offset"]
        if typeForScaledInt(field) == "Float":
            ret = str(ret) + "f"
    return ret

def getMath(x, field, cast, floatTag=""):
    ret = x
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s.toInt().to%s()" % (ret, cast)
    if "Scale" in field:
        ret = "(%s * %s)" % (ret, fieldScale(field))
    if "Offset" in field:
        ret = "(%s + %s)" % (ret, fieldOffset(field))
    if typeForScaledInt(field) == "Float":
        ret = ret+".toFloat()"
    return ret

def setMath(x, field, cast=None, floatTag=""):
    ret = x
    if "Offset" in field:
        ret = "(%s - %s)" % (ret, fieldOffset(field))
    if "Scale" in field:
        ret = "(%s / %s)" % (ret, fieldScale(field))
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s.to%s()" % (ret, cast)
    return ret

def getFn(field):
    loc = str(MsgParser.fieldLocation(field))
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += " + index*" + str(MsgParser.fieldArrayElementOffset(field))
        param += "index: Int"
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    ret = '''\
%s
fun get%s(%s): %s {
''' % (fnHdr(field), field["Name"], param, retType)
    access = "data.get%s(%s%s)" % (fieldType(field), loc, endian_string())
    if ("Offset" in field or "Scale" in field):
        ret += '    val valI : '+fieldType(field)+' = '+access+'\n'
        access = getMath("valI", field, "Double")
        ret += '    val valD = '+access+'\n'
        ret += '    return valD\n'
    else:
        ret += '    return %s\n' % (access)
    ret += '}'
    if MsgParser.fieldUnits(field) == "ASCII" and MsgParser.fieldCount(field) > 1 and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
fun get%sString(): String {
    var value = ""
    for (i in 0 until minOf(%s, header.getDataLength().toInt() - %s)) {
        val nextChar = get%s(i)
        if (nextChar == 0.toUByte()) {
            break
        }
        value += nextChar.toByte().toChar()
    }
    return value
}''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), str(MsgParser.fieldLocation(field)), field["Name"])
    return ret

def setFn(field):
    paramType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        paramType = typeForScaledInt(field)
    valueString = setMath("value", field, fieldType(field))
    param = "value: " + paramType
    loc = str(MsgParser.fieldLocation(field))
    if MsgParser.fieldCount(field) > 1:
        loc += " + index*" + str(MsgParser.fieldArrayElementOffset(field))
        param += ", index: Int"
    ret = '''\
%s
fun set%s(%s) {
    data.put%s(%s, %s%s)
}''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, valueString, endian_string())
    return ret

def getBitsFn(field, bits, bitOffset, numBits):
    # Kotlin currently only supports bitwise operators for Int, so we are gonna convert the inputs to Int first, 
    # apply the bit operators, and then convert the final result to the actual type
    access = "((get%s().toInt() ushr %s) and %s).to%s()" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits), bitParamType(field, bits))
    param = ""
    ret = '''\
%s
fun get%s(%s): %s {
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, bitParamType(field, bits))
    if ("Offset" in bits or "Scale" in bits):
        ret += '    val valI = '+access+'\n'
        access = getMath("valI", bits, "Double")
        ret += '    val valD = '+access+'\n'
        ret += '    return valD\n'
    else:
        ret += '    return %s\n' % (access)

    ret += '}'
    return ret

def setBitsFn(field, bits, bitOffset, numBits):
    param = "value: " + bitParamType(field, bits)
    ret = '''\
%s
fun set%s(%s) {
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param)
    valueString = setMath("value", bits)
    # Kotlin currently only supports bitwise operators for Int, so we are gonna convert the inputs to Int first, 
    # apply the bit operators, and then convert the final result to the actual type
    ret += '''\
    var valI = get%s().toInt() // read
    valI = valI and (%s shl %s).inv() // clear our bits
    valI = valI or ((%s.toInt() and %s) shl %s) // set our bits
    set%s(valI.to%s()) // write
''' % (field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset), field["Name"], paramType(field))
    ret += '}'
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

def initField(field):
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for (i in 0 until "+str(MsgParser.fieldCount(field))+") {\n"
            ret += "    set" + field["Name"] + "(" + str(field["Default"]) + literalSuffix(field) + ", i)\n"
            ret += "}\n"
            return ret
        else:
            return  "set" + field["Name"] + "(" + str(field["Default"]) + literalSuffix(field) + ")"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  "set" + MsgParser.BitfieldName(field, bits) + "(" +str(bits["Default"]) + literalSuffixForBitfield(field, bits) + ")"
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

def optionValue(option):
    ret = int(option["Value"])
    if ret > 2**31:
        return str(ret)+"L"
    return str(ret)

def enums(e):
    ret = ""
    for enum in e:
        ret +=  "enum class " + enum["Name"]+"(override val value: Long): MessageEnum {\n"
        ret += "    "
        for option in enum["Options"]:
            ret += OptionName(option)+"("+str(optionValue(option)) + '), '
        ret = ret[:-2]
        ret += ";\n"
        ret += '''\
    companion object {
        fun construct(value: Long): %s {
            return values().first { it.value == value }
        }
    }
}\n''' % (enum["Name"])
    return ret

def fieldMin(field):
    val = MsgParser.fieldMin(field)
    ret = str(val)
    if ret == 'DBL_MIN':
        ret = 'Double.MIN_VALUE'
    elif ret == 'FLT_MIN':
        ret = 'Float.MIN_VALUE'
    return ret

def fieldMax(field):
    val = MsgParser.fieldMax(field)
    ret = str(val)
    if ret == 'DBL_MAX':
        ret = 'Double.MAX_VALUE'
    elif ret == 'FLT_MAX':
        ret = 'Float.MAX_VALUE'
    return ret

def genericInfo(field, loc, type):
    params  = '    const val loc = ' + loc + '\n'
    params += '    val max = ' + str(fieldMax(field)) + '\n'
    params += '    val min = ' + str(fieldMin(field)) + '\n'
    params += '    const val units = "' + str(MsgParser.fieldUnits(field)) + '"' + '\n'
    params += '    const val count = ' + str(MsgParser.fieldCount(field)) + '\n'
    if "Default" in field:
        params += '    const val '+type+' defaultValue = ' + str(field["Default"]) + "\n" 
    if "Scale" in field:
        params += '    const val scale = ' + str(field["Scale"]) + '\n'
    if "Offset" in field:
        params += '    const val offset = ' + str(field["Offset"]) + '\n'
    return params
    
def fieldInfo(field):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'object ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, str(MsgParser.fieldLocation(field)), retType)
    params += '}\n'
    return params

def fieldBitsInfo(field, bits, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'object ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, str(MsgParser.fieldLocation(field)), retType)
    params += '    const val bitOffset = ' + str(bitOffset) + '\n'
    params += '    const val numBits   = ' + str(numBits) + '\n'
    params += '}\n'
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
    prefix = "var ret: UInt = 0u\n"
    mods = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = str(field["IDBits"])
                getStr = "get"+field["Name"]+"().toUInt()"
                if mods:
                    mods += "ret = ret shl " + numBits + "\n"
                mods += "ret += " + getStr + "\n"
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = str(bitfield["IDBits"])
                        getStr = "get"+BitfieldName(field, bitfield)+"().toUInt()"
                        if mods:
                            mods += "ret = ret shl " + numBits + "\n"
                        mods += "ret += " + getStr + "\n"
    return prefix + mods + "return ret"
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nret = ret shr " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "ret and "+Mask(numBits)+literalSuffix(field)
                setStr = "("+setStr+").to%s()" % fieldType(field)
                ret +=  "set"+field["Name"]+"("+setStr+")"
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = ret shr " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "ret and "+Mask(numBits)+literalSuffix(field)
                        setStr = "("+setStr+").to%s()" % fieldType(field)
                        ret +=  "set"+bitfield["Name"]+"("+setStr+")"
    if ret.count('\n') > 1:
        ret = "var ret = id\n" + ret
    else:
        ret = "val ret = id\n" + ret
    return ret
