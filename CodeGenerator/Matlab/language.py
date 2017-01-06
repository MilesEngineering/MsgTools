import MsgParser
from MsgUtils import *

def Mask(numBits):
    return str(2 ** numBits - 1)

def fieldType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return typeStr
    if str.lower(typeStr) == "float32":
        return "single";
    if str.lower(typeStr) == "float64":
        return "double";
    return "?"

def fnHdr(field):
    ret = "%% %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "single"

def getFn(field, offset):
    loc = str(offset)
    end_loc = str(offset + MsgParser.fieldSize(field)*MsgParser.fieldCount(field)-1)
    param = "obj"
    access = "swapbytes(typecast(obj.m_data(%s:%s), '%s'))" % (loc, end_loc, fieldType(field))
    access = getMath(access, field, typeForScaledInt(field))
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    ret = '''\
%s
function ret = get.%s(%s)
    ret = %s;
''' % (fnHdr(field), field["Name"], param, access)
    if "Enum" in field:
        ret += "    if isKey(obj."+field["Enum"]+", ret)\n"
        ret += "        ret = obj."+field["Enum"]+"(ret);\n"
        ret += "    end\n"
    ret += "end\n"
    return ret

def setFn(field, offset):
    valueString = setMath("value", field, fieldType(field))
    loc = str(offset)
    end_loc = str(offset + MsgParser.fieldSize(field)*MsgParser.fieldCount(field)-1)
    ret = '''\
%s
function obj = set.%s(obj, value)
''' % (fnHdr(field), field["Name"])
    if "Enum" in field:
        ret += "    if isKey(obj.Reverse"+field["Enum"]+", value)\n"
        ret += "        value = obj.Reverse"+field["Enum"]+"(value);\n"
        ret += "    end\n"
    ret += '''\
    obj.m_data(%s:%s) = typecast(swapbytes(%s(%s)), 'uint8');
end''' % (loc, end_loc, fieldType(field), valueString)
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "bitand(bitshift(obj.%s, -%s), %s)" % (field["Name"], str(bitOffset), Mask(numBits))
    access = getMath(access, bits, typeForScaledInt(bits))
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)
    ret = '''\
%s
function ret = get.%s(obj)
    ret = %s;
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), access)
    if "Enum" in bits:
        ret += "    if isKey(obj."+bits["Enum"]+", ret)\n"
        ret += "        ret = obj."+bits["Enum"]+"(ret);\n"
        ret += "    end\n"
    ret += "end\n"
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    paramType = fieldType(field)
    valueString = setMath("value", bits, fieldType(field))
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    ret = '''\
%s
function obj = set.%s(obj, value)
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits))
    if "Enum" in field:
        ret += "    if isKey(obj.Reverse"+field["Enum"]+", value)\n"
        ret += "        value = obj.Reverse"+field["Enum"]+"(value);\n"
        ret += "    end\n"
    ret += '''\
    obj.%s = bitor(bitand(obj.%s, bitcmp(bitshift(%s(%s),%s))), (bitshift((bitand(%s, %s)), %s)));
end''' % (field["Name"], field["Name"], fieldType(field), Mask(numBits), str(bitOffset), valueString, Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 1
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

def enums(e):
    ret = ""
    for enum in e:
        # forward enum
        fwd = enum["Name"]+" = containers.Map({...\n"
        for option in enum["Options"]:
            fwd += "    " + str(option["Value"]) + ",\n"
        fwd = fwd[:-2]
        fwd += "}, {\n"
        for option in enum["Options"]:
            fwd += "    '" + option["Name"] + "',\n"
        fwd = fwd[:-2]
        fwd += "});\n"

        # Reverse enum
        back = "Reverse" + enum["Name"]+" = {"
        back = "Reverse" + enum["Name"]+" = containers.Map(values(<MSGNAME>."+enum["Name"]+"), keys(<MSGNAME>."+enum["Name"]+"));\n"

        ret += fwd + back
    return ret

def declarations(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(field["Name"] + ";")
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append(bits["Name"] + ";")
    return ret

def fieldDefault(field):
    if "Default" in field:
        return str(field["Default"])
    # should be based on type
    return "0"

def initField(field):
    defaultValue = fieldType(field) + "("+ fieldDefault(field) +")"
    if MsgParser.fieldCount(field) > 1:
        ret =  "for index="+str(MsgParser.fieldCount(field))+": -1: 1\n"
        ret += "    obj." + field["Name"] + "(index) = " + defaultValue + ";\n"
        ret += "end"
        return ret
    else:
        return  "obj." + field["Name"] + " = " + defaultValue + ";"

def initBitfield(field, bits):
    paramType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    defaultValue = paramType + "("+ fieldDefault(bits) +")"
    return  "obj." + MsgParser.BitfieldName(field, bits) + " = " +defaultValue + ";"

def initCode(msg):
    ret = []
    
    offset = 1
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

def undefinedMsgId():
    return "-1"

def addShift(base, value, shiftValue):
    ret = value
    if base != "":
        ret = "bitshift("+base+", "+str(shiftValue)+")"+"+"+value
    return ret

def getMsgID(msg):
    ret = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = field["IDBits"]
                if "Enum" in field and enumAsIntParam:
                    pass
                getStr = "obj."+field["Name"]
                if "Enum" in field and castEnums:
                    getStr = "uint32_t("+getStr+")"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        if "Enum" in bitfield and enumAsIntParam:
                            pass
                        getStr = "obj."+BitfieldName(field, bitfield)
                        if "Enum" in bitfield and castEnums:
                            getStr = "uint32_t("+getStr+")"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nid = id >> " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "bitand(id, "+Mask(numBits)+")"
                if "Enum" in field and castEnums:
                    setStr = field["Enum"]+"("+setStr+")"
                ret +=  "obj."+field["Name"]+" = "+setStr
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = id >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "bitand(id, "+Mask(numBits)+")"
                        if "Enum" in bitfield and castEnums:
                            setStr = bitfield["Enum"]+"("+setStr+")"
                        ret +=  "obj."+bitfield["Name"]+" = "+setStr
    return ret

