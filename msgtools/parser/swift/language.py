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
    if str.lower(typeStr) == "float32":
        return "Float";
    if str.lower(typeStr) == "float64":
        return "Double";
    return "?"

def fieldType(field):
    return paramType(field)

def bitParamType(field, bitfield):
    ret = paramType(field)
    if "Offset" in bitfield or "Scale" in bitfield:
        return typeForScaledInt(field)
    return ret

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "Double"
    return "Float"

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

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "_ idx: Int"
    if "Enum" in field:
        if param != "":
            param += ", "
        param += "_ enumAsInt:Bool=false"
    access = "(m_data.get%s(%s))" % (fieldType(field), loc)
    access = getMath(access, field, "")
    ret = '''\
%s
public func Get%s(%s) -> %s
{
    return %s;
};''' % (fnHdr(field), field["Name"], param, paramType(field), access)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
public func Get%sString() -> String
{
    var value = "";
    for i in 0 ..< min(%s, hdr.GetDataLength()-%s)
    {
        var nextChar = String.fromCharCode(Get%s(i));
        if(nextChar == "\\0")
        {
            break;
        }
        value += nextChar;
    }
    return value;
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), offset, field["Name"])
    return ret

def setFn(field, offset):
    valueString = setMath("value", field, "")
    param = "_ value: " + paramType(field)
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", _ idx: Int"
    ret = '''\
%s
public func Set%s(%s)
{
    m_data.set%s(%s, %s);
};''' % (fnHdr(field), field["Name"], param, fieldType(field), loc, valueString)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
public func Set%sString(value: String)
{
    for i in 0 ..< min(%s, value.characters.count)
    {
        Set%s(value[i].charCodeAt(0), i);
    }
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), field["Name"])
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, "")
    param = ""
    if "Enum" in bits:
        param += "_ enumAsInt:Bool=false"
    ret = '''\
%s
public func Get%s(%s) -> %s
{
    return %s;
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, bitParamType(field, bits), access)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    valueString = setMath("value", bits, "")
    param = "_ value: " + bitParamType(field, bits)
    ret = '''\
%s
public func Set%s(%s)
{
    Set%s((Get%s() & ~(%s << %s)) | ((%s & %s) << %s));
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset))
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
            ret = "for (i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "{\n"
            ret += "    Set" + field["Name"] + "(" + str(field["Default"]) + ", i);" 
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
        # enum
        fwd = "public enum " + enum["Name"]+"Values: Int {\n"
        for option in enum["Options"]:
            fwd += "    case "+str(option["Name"]) + " = "+str(option["Value"])+";\n"
        fwd += "}\n"

        # forward map
        fwd += "public let "+enum["Name"]+"Enum = ["
        for option in enum["Options"]:
            fwd += '"'+str(option["Name"])+'"' +': '+str(option["Value"]) + ', '
        fwd = fwd[:-2]
        fwd += "]\n"
        
        # Reverse map
        back = "public let Reverse" + enum["Name"]+"Enum = ["
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

def swiftGetMsgID(prefix, baseParam, castEnums, enumAsIntParam, msg):
    ret = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = field["IDBits"]
                param = baseParam
                if "Enum" in field and enumAsIntParam:
                    if param != "":
                        param += ", "
                    param += "1"
                getStr = prefix+"Get"+field["Name"]+"("+param+")"
                if "Enum" in field and castEnums:
                    getStr = "uint32_t("+getStr+")"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        param = baseParam
                        if "Enum" in bitfield and enumAsIntParam:
                            if param != "":
                                param += ", "
                            param += "1"
                        getStr = prefix+"Get"+BitfieldName(field, bitfield)+"("+param+")"
                        if "Enum" in bitfield and castEnums:
                            getStr = "uint32_t("+getStr+")"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def swiftSetMsgID(prefix, param, castEnums, enumAsIntParam, msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nret = ret >> " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "ret & "+Mask(numBits)
                if "Enum" in field and castEnums:
                    setStr = field["Enum"]+"("+setStr+")"
                setStr = fieldType(field)+"("+setStr+")"
                ret +=  prefix+"Set"+field["Name"]+"("+param+setStr+")"
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = ret >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "ret & "+Mask(numBits)
                        if "Enum" in bitfield and castEnums:
                            setStr = bitfield["Enum"]+"("+setStr+")"
                        setStr = fieldType(field)+"("+setStr+")"
                        ret +=  prefix+"Set"+bitfield["Name"]+"("+param+setStr+")"
    if ret.count('\n') > 1:
        ret = "var ret = id\n" + ret
    else:
        ret = "let ret = id\n" + ret
    return ret

def getMsgID(msg):
    return swiftGetMsgID("", "", False, True, msg)
    
def setMsgID(msg):
    return swiftSetMsgID("", "", False, True, msg)

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
                        ret.append("    for i in 0 ..<"+str(MsgParser.fieldCount(field)))
                        ret.append("    for(var i=0; i<"+str(MsgParser.fieldCount(field))+"; i++)")
                        ret.append('        ret["'+field["Name"] + '"][i] = Get' + field["Name"] + "(i);")
                        ret.append('} catch (err) {}')
            
    return "\n".join(ret)
