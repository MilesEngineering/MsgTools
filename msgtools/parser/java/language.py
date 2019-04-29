import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def fieldType(field):
    fieldTypeDict = \
    {"uint64":"error", "uint32":"long","uint16": "int",   "uint8": "short",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "byte",
      "float64":"double", "float32":"float"}
    typeStr = field["Type"]
    return fieldTypeDict[typeStr]

def fieldAccessorType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"int", "uint16": "short", "uint8": "",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "",
      "float64":"double", "float32":"float"}
    typeStr = field["Type"]
    type = fieldTypeDict[typeStr]
    return type.capitalize()

def fieldCastType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"int", "uint16": "short", "uint8": "byte",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "byte",
      "float64":"double", "float32":"float"}
    typeStr = field["Type"]
    type = fieldTypeDict[typeStr]
    return type.capitalize()

def fieldPromotionFn(field):
    fieldTypeDict = \
    {"uint64":"error", "uint32":"FieldAccess.toUnsignedLong", "uint16": "FieldAccess.toUnsignedInt", "uint8": "FieldAccess.toUnsignedInt"}
    typeStr = field["Type"]
    return fieldTypeDict[typeStr]

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "float"

def getFn(field):
    loc = str(MsgParser.fieldLocation(field))
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += "int idx"
    access = "m_data.get%s(%s)" % (fieldAccessorType(field), loc)
    if field["Type"].startswith("u"):
        access = fieldPromotionFn(field)+"("+access+")"
    access = "("+fieldType(field)+")"+access
    access = getMath(access, field, "("+typeForScaledInt(field)+")", 'f')
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    #elif "Enum" in field:
    #    retType = field["Enum"]
    #    access = retType + ".construct(" + access + ")"
    ret = '''\
%s
public %s Get%s(%s)
{
    return %s;
}''' % (fnHdr(field), retType, field["Name"], param, access)
    return ret

def setFn(field):
    paramType = fieldType(field)
    valueString = setMath("value", field, '('+fieldType(field)+')', 'f')
    if "Offset" in field or "Scale" in field:
        paramType = typeForScaledInt(field)
    #elif "Enum" in field:
    #    valueString = valueString + ".intValue()"
    #    paramType = field["Enum"]
    param = paramType + " value"
    loc = str(MsgParser.fieldLocation(field))
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += ", int idx"
    ret = '''\
%s
public void Set%s(%s)
{
    m_data.put%s(%s, (%s)%s);
}''' % (fnHdr(field), field["Name"], param, fieldAccessorType(field), loc, fieldCastType(field).lower(), valueString)
    return ret

def getBitsFn(field, bits, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, "("+typeForScaledInt(bits)+")", 'f')
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)
    #elif "Enum" in bits:
    #    retType = bits["Enum"]
    #    access = retType + ".construct(" + access + ")"
    else:
        access = "("+retType+")" + "(" + access + ")"
    ret = '''\
%s
public %s Get%s()
{
    return %s;
}''' % (fnHdr(bits), retType, MsgParser.BitfieldName(field, bits), access)
    return ret

def setBitsFn(field, bits, bitOffset, numBits):
    paramType = fieldType(field)
    intType = paramType
    valueString = setMath("value", bits, '('+fieldType(field)+')', 'f')
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    #elif "Enum" in bits:
    #    valueString = valueString + ".intValue()"
    #    paramType = bits["Enum"]
    ret = '''\
%s
public void Set%s(%s value)
{
    Set%s((%s)((Get%s() & ~(%s << %s)) | ((%s & %s) << %s)));
}''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), paramType, field["Name"], intType, field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset))
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

def languageConst(value):
    ret = value
    if isinstance(ret, str) and ret.isdigit():
        ret = int(ret)
    if isinstance(ret, int):
        if(ret > 2**31):
            ret = str(ret)+"L"
        else:
            ret = str(ret)
    elif not isinstance(ret, str):
        ret = str(ret)
    return ret

def initField(field):
    type = fieldType(field)
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for (int i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "    Set%s((%s)%s, i);" % (field["Name"], type, languageConst(field["Default"])) 
            return ret;
        else:
            return  "Set%s((%s)%s);" % (field["Name"],type, languageConst(field["Default"]))
    return ""

def initBitfield(field, bits):
    type = fieldType(field)
    if "Default" in bits:
        return  "Set%s((%s)%s);" % (MsgParser.BitfieldName(field, bits), type, str(bits["Default"]))
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
        ret +=  "public enum " + enum["Name"]+" {\n"
        ret += "    "
        for option in enum["Options"]:
            ret += OptionName(option)+"("+str(optionValue(option)) + '), '
        ret = ret[:-2]
        ret += ";\n"
        ret += '''\
    private final long id;
    {0}(long id) {{ this.id = id; }}
    static Map<Long, {0}> map = new HashMap<>();
    static {{
        for ({0} key : {0}.values()) {{
            map.put(key.id, key);
        }}
    }}
    public long intValue() {{ return id; }}
    public static {0} construct(long value) {{ return map.get(value); }}
}}\n'''.format(enum["Name"])
    return ret

def fieldReflection(field):
    loc = str(MsgParser.fieldLocation(field))
    params = "FieldInfo";
    params += "("
    params += '"'+field["Name"] + '"'
    params += ', "' + MsgParser.fieldDescription(field) + '"'
    params += ', "' + MsgParser.fieldUnits(field) + '"'
    params += ", " + str(MsgParser.fieldCount(field))
    params += ")"
    return params

def fieldBitsReflection(field, bits, bitOffset, numBits):
    loc = str(MsgParser.fieldLocation(field))
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
    val = MsgParser.fieldMin(field)
    ret = str(val)
    if ret == 'DBL_MIN':
        ret = 'Double.MIN_VALUE'
    elif ret == 'FLT_MIN':
        ret = 'Float.MIN_VALUE'
    else:
        try:
            if val > fieldStorageMax("uint32"):
                ret += 'L'
        except TypeError:
            pass
    return ret

def fieldMax(field):
    val = MsgParser.fieldMax(field)
    ret = str(val)
    if ret == 'DBL_MAX':
        ret = 'Double.MAX_VALUE'
    elif ret == 'FLT_MAX':
        ret = 'Float.MAX_VALUE'
    else:
        try:
            if val > fieldStorageMax("int32"):
                ret += 'L'
        except TypeError:
            pass
    return ret

def genericInfo(field, loc, type):
    params  = '    public static final int loc = ' + loc + ';\n'
    params += '    public static final %s max = (%s)%s;\n' % (type, type, fieldMax(field))
    params += '    public static final %s min = (%s)%s;\n' % (type, type, fieldMin(field))
    params += '    public static final String units = "' + str(MsgParser.fieldUnits(field)) + '"' + ';\n'
    params += '    public static final int count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += '    public static final %s defaultValue = (%s)%s;\n' % (type, type, languageConst(field["Default"]))
    if "Scale" in field:
        params += '    public static final float scale = (float)' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += '    public static final float offset = (float)' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'public class ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, str(MsgParser.fieldLocation(field)), retType)
    params += '};\n'
    return params

def fieldBitsInfo(field, bits, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'public class ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, str(MsgParser.fieldLocation(field)), retType)
    params += '    public static final int bitOffset = ' + str(bitOffset) + ';\n'
    params += '    public static final int numBits   = ' + str(numBits) + ';\n'
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

def declarations(msg):
    return []

def getMsgID(msg):
    ret = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = field["IDBits"]
                param = ""
                getStr = "Get"+field["Name"]+"("+param+")"
                #if "Enum" in field:
                #    getStr = getStr+".intValue()"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        param = ""
                        getStr = "Get"+BitfieldName(field, bitfield)+"("+param+")"
                        #if "Enum" in bitfield:
                        #    getStr = getStr+".intValue()"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            type = fieldType(field)
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nid = id >> " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "id & "+Mask(numBits)
                #if "Enum" in field:
                #    setStr = field["Enum"]+".construct("+setStr+")"
                #else:
                setStr = "("+type+")("+setStr+")"
                ret +=  "Set"+field["Name"]+"("+setStr+")"
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = id >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "id & "+Mask(numBits)
                        #if "Enum" in bitfield:
                        #    setStr = bitfield["Enum"]+".construct("+setStr+")"
                        #else:
                        setStr = "("+type+")("+setStr+")"
                        ret +=  "Set"+bitfield["Name"]+"("+setStr+")"
    return ret

oneOutputFilePerMsg = True
