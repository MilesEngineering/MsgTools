import MsgParser
from MsgUtils import *

# https://www.html5rocks.com/en/tutorials/webgl/typed_arrays/
# https://github.com/kig/DataStream.js
# https://www.html5rocks.com/en/tutorials/websockets/basics/

def fieldType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"long","uint16": "int",   "uint8": "short",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "char",
      "float64":"double", "float32":"float"}
    typeStr = str.lower(field["Type"])
    return field["Type"].capitalize()

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "float"

def enumLookup(field):
    lookup  = "defaultValue = 0\n"
    lookup += "    try:\n"
    lookup += "        value = int(float(value))\n"
    lookup += "    except ValueError:\n"
    lookup += "        pass\n"
    lookup += "    if isinstance(value, int) or value.isdigit():\n"
    lookup += "        defaultValue = int(value)\n"
    lookup += "    value = <MSGNAME>." + str(field["Enum"]) + ".get(value, defaultValue)\n"
    lookup += "    "
    return lookup

def reverseEnumLookup(field):
    lookup = "if not enumAsInt:\n"
    lookup += "        value = <MSGNAME>.Reverse" + str(field["Enum"]) + ".get(value, value)\n    "
    return lookup

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "idx"
    if "Enum" in field:
        if param != "":
            param += ", "
        param += "enumAsInt=0"
    access = "(this.m_data.get%s(%s, false))" % (fieldType(field), loc)
    access = getMath(access, field, "")
    if "Enum" in field:
        cleanup = reverseEnumLookup(field)
    ret = '''\
%s
<MSGNAME>.prototype.Get%s = function(%s)
{
    return %s;
};''' % (fnHdr(field), field["Name"], param, access)
    return ret

def setFn(field, offset):
    valueString = setMath("value", field, "")
    lookup = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        lookup = enumLookup(field)        
    param = "value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", idx"
    ret = '''\
%s
<MSGNAME>.prototype.Set%s = function(%s)
{
    this.m_data.set%s(%s, %s, false);
};''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, valueString)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(this.Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, "")
    param = ""
    if "Enum" in bits:
        param += "enumAsInt=0"
    if "Enum" in bits:
        cleanup = reverseEnumLookup(bits)
    ret = '''\
%s
<MSGNAME>.prototype.Get%s = function(%s)
{
    return %s;
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, access)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    valueString = setMath("value", bits, "")
    lookup = ""
    if "Enum" in bits:
        # find index that corresponds to string input param
        lookup = enumLookup(bits)
    ret = '''\
%s
<MSGNAME>.prototype.Set%s = function(value)
{
    this.Set%s((this.Get%s() & ~(%s << %s)) | ((%s & %s) << %s));
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset))
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
        # forward enum
        fwd = "var " + enum["Name"]+" = {};\n"
        for option in enum["Options"]:
            fwd += enum["Name"] + "[\"" + str(option["Name"]) + "\"] = "+str(option["Value"])+";\n"

        # Reverse enum
        back = "var Reverse" + enum["Name"]+" = {};\n"
        back += "for(key in "+enum["Name"]+") {\n"
        back += "    Reverse" + enum["Name"] + "["+enum["Name"]+"[key]" +"] = key;\n"
        back += "}\n"

        ret += fwd + back
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
    
def declarations(msg):
    return []

def getMsgID(msg):
    return baseGetMsgID("this.", "", 0, 1, msg)
    
def setMsgID(msg):
    return baseSetMsgID("this.", "", 0, 1, msg)
