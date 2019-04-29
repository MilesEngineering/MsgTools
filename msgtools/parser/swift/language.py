import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def paramType(field):
    typeStr = field["Type"]
    # need to capitalize first 1-2 letters
    if "int" in typeStr:
        if "Offset" in field or "Scale" in field:
            return typeForScaledInt(field)
        typeStr = typeStr.replace("u", "U")
        typeStr = typeStr.replace("i", "I")
        return typeStr
    if typeStr == "float32":
        return "Float";
    if typeStr == "float64":
        return "Double";
    return "?"

def fieldType(field):
    typeStr = field["Type"]
    # need to capitalize first 1-2 letters
    if "int" in typeStr:
        typeStr = typeStr.replace("u", "U")
        typeStr = typeStr.replace("i", "I")
        return typeStr
    if typeStr == "float32":
        return "Float";
    if typeStr == "float64":
        return "Double";
    return "?"

def bitParamType(field, bitfield):
    ret = paramType(field)
    if "Offset" in bitfield or "Scale" in bitfield:
        return typeForScaledInt(field)
    return ret

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    return "Double"

def enumLookup(field):
    lookup  = "if("+ str(field["Enum"])+"Enum.keys.contains(value))\n"
    lookup += "    {\n"
    lookup += "        value = "+ str(field["Enum"])+"Enum[value];\n"
    lookup += "    }\n"
    lookup += "    "
    return lookup

def reverseEnumLookup(field):
    lookup = "if(!enumAsInt)\n"
    lookup += "{\n"
    lookup += "        if(Reverse"+ str(field["Enum"])+"Enum.keys.contains(value))\n"
    lookup += "        {\n"
    lookup += "            value = Reverse" + str(field["Enum"]) + "Enum[value];\n    "
    lookup += "        }\n"
    lookup += "}\n"
    return lookup

def getFn(field):
    loc = str(MsgParser.fieldLocation(field))
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += "_ idx: Int"
    ret = '''\
%s
public func Get%s(%s) -> %s
{
''' % (fnHdr(field), field["Name"], param, paramType(field))
    access = "m_data.GetField(offset: %s)" % (loc)
    if ("Offset" in field or "Scale" in field):
        ret += '    let valI : '+fieldType(field)+' = '+access+';\n'
        access = getMath("valI", field, "Double")
        ret += '    let valD = '+access+';\n'
        ret += '    return valD;\n'
    else:
        ret += '    return %s;\n' % (access)
    ret += '};'
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
public func Get%sString() -> String
{
    var value = "";
    for i in 0 ..< min(%s, hdr.GetDataLength()-%s)
    {
        let nextChar = Get%s(Int(i));
        if(nextChar == 0)
        {
            break;
        }
        value += String(nextChar);
    }
    return value;
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), str(MsgParser.fieldLocation(field)), field["Name"])
    return ret

def setFn(field):
    valueString = setMath("value", field, fieldType(field))
    param = "_ value: " + paramType(field)
    loc = str(MsgParser.fieldLocation(field))
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldArrayElementOffset(field))
        param += ", _ idx: Int"
    ret = '''\
%s
public func Set%s(%s)
{
    m_data.SetField(offset: %s, value: %s);
};''' % (fnHdr(field), field["Name"], param, loc, valueString)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
public func Set%sString(value: String)
{
    let stringArray = Array(value.utf8);
    for i in 0 ..< min(%s, stringArray.count)
    {
        Set%s(stringArray[i], i);
    }
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), field["Name"])
    return ret

def getBitsFn(field, bits, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    param = ""
    ret = '''\
%s
public func Get%s(%s) -> %s
{
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, bitParamType(field, bits))
    if ("Offset" in bits or "Scale" in bits):
        ret += '    let valI = '+access+';\n'
        access = getMath("valI", bits, "Double")
        ret += '    let valD = '+access+';\n'
        ret += '    return valD;\n'
    else:
        ret += '    return %s;\n' % (access)

    ret += '};'
    return ret

def setBitsFn(field, bits, bitOffset, numBits):
    param = "_ value: " + bitParamType(field, bits)
    ret = '''\
%s
public func Set%s(%s)
{
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param)

    valueString = setMath("value", bits, fieldType(field))
    ret += '''\
    var valI = Get%s(); // read
    valI = valI & ~(%s << %s); // clear our bits
    valI = valI | ((%s & %s) << %s); // set our bits
    Set%s(valI); // write
''' % (field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset), field["Name"])
    ret += '};'
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
            ret = "for i in 0 ..< "+str(MsgParser.fieldCount(field))+"\n"
            ret += "{\n"
            ret += "    Set" + field["Name"] + "(" + str(field["Default"]) + ", i);\n"
            ret += "}\n"
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
        if enum["Name"] == "IDs":
            for option in enum["Options"]:
                ret += "static let MSG_ID_" + option["Name"] + " = "+str(option["Value"])+";\n"
        else:
            # enum
            fwd = "public enum " + enum["Name"]+"Values: Int {\n"
            for option in enum["Options"]:
                fwd += "    case "+str(option["Name"]) + " = "+str(option["Value"])+";\n"
            fwd += "}\n"

            # forward map
            fwd += "public static let "+enum["Name"]+"Enum = ["
            for option in enum["Options"]:
                fwd += '"'+str(option["Name"])+'"' +': '+str(option["Value"]) + ', '
            fwd = fwd[:-2]
            fwd += "]\n"
            
            # Reverse map
            back = "public static let Reverse" + enum["Name"]+"Enum = ["
            for option in enum["Options"]:
                back += str(option["Value"]) +': "'+str(option["Name"]) + '", '
            back = back[:-2]
            back += "]\n"

            ret += fwd+back
    return ret

def reflectionInterfaceType(field):
    type = field["Type"]
    if "float" in type or "Offset" in field or "Scale" in field:
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitsReflectionInterfaceType(field):
    type = "int"
    if "Offset" in field or "Scale" in field:
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitfieldReflection(msg, field, bits):
    name = bits["Name"]
    ret = "["+\
              '"name":"'+name + '",'+\
              '"type":"'+bitsReflectionInterfaceType(bits) + '",'+\
              '"units":"'+MsgParser.fieldUnits(bits) + '",'+\
              '"minVal":"'+str(MsgParser.fieldMin(bits)) + '",'+\
              '"maxVal":"'+str(MsgParser.fieldMax(bits)) + '",'+\
              '"description":"'+MsgParser.fieldDescription(bits) + '",'+\
              '"get":"Get' + name + '",'+\
              '"set":"Set' + name  + '", '
    if "Enum" in bits:
        ret += '"enumLookup" : ['+  bits["Enum"]+"Enum, " + "Reverse" + bits["Enum"]+"Enum]]"
    else:
        ret += '"enumLookup" : []]'
    return ret

def fieldReflection(msg, field):
    fieldFnName = field["Name"]
    fieldCount = MsgParser.fieldCount(field)
    if MsgParser.fieldCount(field) != 1 and MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        fieldFnName = field["Name"]+"String"
        fieldCount = 1
    fieldInfo = "["+\
                  '"name":"'+field["Name"] + '",'+\
                  '"type":"'+reflectionInterfaceType(field) + '",'+\
                  '"units":"'+MsgParser.fieldUnits(field) + '",'+\
                  '"minVal":"'+str(MsgParser.fieldMin(field)) + '",'+\
                  '"maxVal":"'+str(MsgParser.fieldMax(field)) + '",'+\
                  '"description":"'+MsgParser.fieldDescription(field) + '",'+\
                  '"get":"Get' + fieldFnName + '",'+\
                  '"set":"Set' + fieldFnName  + '",'+\
                  '"count":'+str(fieldCount) + ', '
    if "Bitfields" in field:
        bitfieldInfo = []
        for bits in field["Bitfields"]:
            bitfieldInfo.append("    " + bitfieldReflection(msg, field, bits))
        fieldInfo += '"bitfieldInfo" : [\n' + ",\n".join(bitfieldInfo) + "], "
    else:
        fieldInfo += '"bitfieldInfo" : [], '
    if "Enum" in field:
        fieldInfo += '"enumLookup" : [' + field["Enum"]+"Enum, " + "Reverse" + field["Enum"]+"Enum]]"
    else:
        fieldInfo += '"enumLookup" : []]'
    return fieldInfo

def reflection(msg):
    fieldInfos = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInfos.append(fieldReflection(msg, field))
    return ",\n".join(fieldInfos)

def genericInfo(field, loc, type):
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
    
def fieldInfo(field):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'class ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, str(MsgParser.fieldLocation(field)), retType)
    params += '};\n'
    return params

def fieldBitsInfo(field, bits, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'class ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, str(MsgParser.fieldLocation(field)), retType)
    params += '    static final int bitOffset = ' + str(bitOffset) + ';\n'
    params += '    static final int numBits   = ' + str(numBits) + ';\n'
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
    prefix = "var ret : UInt32 = 0;\n"
    mods = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = str(field["IDBits"])
                getStr = "UInt32(Get"+field["Name"]+"())"
                if mods:
                    mods += "ret = ret << " + numBits + ";\n"
                mods += "ret += " + getStr + ";\n"
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = str(bitfield["IDBits"])
                        getStr = "UInt32(Get"+BitfieldName(field, bitfield)+"())"
                        if mods:
                            mods += "ret = ret << " + numBits + ";\n"
                        mods += "ret += " + getStr + ";\n"
    return prefix + mods + "return ret;"
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nret = ret >> " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "ret & "+Mask(numBits)
                setStr = fieldType(field)+"("+setStr+")"
                ret +=  "Set"+field["Name"]+"("+setStr+")"
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = ret >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "ret & "+Mask(numBits)
                        setStr = fieldType(field)+"("+setStr+")"
                        ret +=  "Set"+bitfield["Name"]+"("+setStr+")"
    if ret.count('\n') > 1:
        ret = "var ret = id\n" + ret
    else:
        ret = "let ret = id\n" + ret
    return ret

def structUnpacking(msg):
    ret = []

    if "Fields" in msg:    
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append('try { ret["'+bits["Name"] + '"] = Get' + bits["Name"] + "(); } catch (err) {}")
            else:
                if MsgParser.fieldCount(field) == 1:
                    ret.append('try { ret["'+field["Name"] + '"] = Get' + field["Name"] + "(); } catch (err) {}")
                else:
                    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
                        ret.append('try { ret["'+field["Name"] + '"] = Get' + field["Name"] + "String(); } catch (err) {}")
                    else:
                        ret.append('try { ret["'+field["Name"] + '"] = []; } catch (err) {}')
                        ret.append('try { ')
                        ret.append("    for i in 0 ..< "+str(MsgParser.fieldCount(field)))
                        ret.append('    {')
                        ret.append('        ret["'+field["Name"] + '"][i] = Get' + field["Name"] + "(i);")
                        ret.append('    }')
                        ret.append('} catch (err) {}')
            
    return "\n".join(ret)
