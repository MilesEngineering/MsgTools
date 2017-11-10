import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def outputSubdir(outDir, filename):
    return outDir + "/+" + filename

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

def matlabFieldName(msg, field):
    fieldName = field["Name"]
    if fieldName == msgShortName(msg):
        fieldName = fieldName + "_"
    return fieldName

def getFn(msg, field, offset):
    loc = str(offset)
    end_loc = str(offset + MsgParser.fieldSize(field)*MsgParser.fieldCount(field)-1)
    param = "obj"
    access = "swapbytes(typecast(obj.m_data(%s:%s), '%s'))" % (loc, end_loc, fieldType(field))
    access = getMath(access, field, typeForScaledInt(field))
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)
    asInt = ""
    if "Enum" in field:
        asInt = "AsInt"
    ret = '''\
%s
function ret = get.%s%s(%s)
    ret = %s;
end
''' % (fnHdr(field), matlabFieldName(msg,field), asInt, param, access)
    if "Enum" in field:
        ret += '''\
%s
function ret = get.%s(%s)
    ret = obj.%sAsInt;
''' % (fnHdr(field), matlabFieldName(msg,field), param, matlabFieldName(msg,field))
        ret += "    if isKey(obj."+field["Enum"]+"Enum, ret)\n"
        ret += "        ret = obj."+field["Enum"]+"Enum(ret);\n"
        ret += "    end\n"
        ret += "end\n"
    return ret

def setFn(msg, field, offset):
    valueString = setMath("value", field, fieldType(field))
    loc = str(offset)
    end_loc = str(offset + MsgParser.fieldSize(field)*MsgParser.fieldCount(field)-1)
    asInt = ""
    if "Enum" in field:
        asInt = "AsInt"
    ret = '''\
%s
function obj = set.%s%s(obj, value)
''' % (fnHdr(field), matlabFieldName(msg,field), asInt)
    ret += '''\
    obj.m_data(%s:%s) = typecast(swapbytes(%s(%s)), 'uint8');
end
''' % (loc, end_loc, fieldType(field), valueString)
    if "Enum" in field:
        ret += '''\
%s
function obj = set.%s(obj, value)
''' % (fnHdr(field), matlabFieldName(msg,field))
        ret += "    if isKey(obj.Reverse"+field["Enum"]+"Enum, value)\n"
        ret += "        value = obj.Reverse"+field["Enum"]+"Enum(value);\n"
        ret += "    end\n"
        ret += "    obj."+matlabFieldName(msg,field)+"AsInt = value;\n"
        ret += "end\n"
    return ret

def getBitsFn(msg, field, bits, offset, bitOffset, numBits):
    access = "bitand(bitshift(obj.%s, -%s), %s)" % (matlabFieldName(msg,field), str(bitOffset), Mask(numBits))
    access = getMath(access, bits, typeForScaledInt(bits))
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)
    asInt = ""
    if "Enum" in bits:
        asInt = "AsInt"
    ret = '''\
%s
function ret = get.%s%s(obj)
    ret = %s;
end
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), asInt, access)
    if "Enum" in bits:
        ret += '''\
%s
function ret = get.%s(obj)
    ret = obj.%sAsInt;
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), MsgParser.BitfieldName(field, bits))
        ret += "    if isKey(obj."+bits["Enum"]+"Enum, ret)\n"
        ret += "        ret = obj."+bits["Enum"]+"Enum(ret);\n"
        ret += "    end\n"
        ret += "end\n"
    return ret

def setBitsFn(msg, field, bits, offset, bitOffset, numBits):
    paramType = fieldType(field)
    valueString = setMath("value", bits, fieldType(field))
    if "Offset" in bits or "Scale" in bits:
        paramType = typeForScaledInt(bits)
    asInt = ""
    if "Enum" in bits:
        asInt = "AsInt"
    ret = '''\
%s
function obj = set.%s%s(obj, value)
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), asInt)
    ret += '''\
    obj.%s = bitor(bitand(obj.%s, bitcmp(bitshift(%s(%s),%s))), (bitshift((bitand(%s, %s)), %s)));
end''' % (matlabFieldName(msg,field), matlabFieldName(msg,field), fieldType(field), Mask(numBits), str(bitOffset), valueString, Mask(numBits), str(bitOffset))
    if "Enum" in bits:
        ret += '''\
%s
function obj = set.%s(obj, value)
''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits))
        ret += "    if isKey(obj.Reverse"+bits["Enum"]+"Enum, value)\n"
        ret += "        value = obj.Reverse"+bits["Enum"]+"Enum(value);\n"
        ret += "    end\n"
        ret += "    obj."+MsgParser.BitfieldName(field, bits)+"AsInt = value;\n"
        ret += "end\n"
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 1
    if "Fields" in msg:
        for field in msg["Fields"]:
            gets.append(getFn(msg,field, offset))
            sets.append(setFn(msg,field, offset))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    gets.append(getBitsFn(msg, field, bits, offset, bitOffset, numBits))
                    sets.append(setBitsFn(msg, field, bits, offset, bitOffset, numBits))
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return gets+sets

def enums(e):
    ret = ""
    for enum in e:
        keys = ""
        for option in enum["Options"]:
            keys += "    " + str(option["Value"]) + ",\n"
        keys = keys[:-2]
        values = ""
        for option in enum["Options"]:
            values += "    '" + option["Name"] + "',\n"
        values = values[:-2]
        # forward enum
        fwd = enum["Name"]+"Enum = containers.Map({...\n"
        fwd += keys
        fwd += "}, {\n"
        fwd += values
        fwd += "});\n"

        # Reverse enum
        back = "Reverse" + enum["Name"]+"Enum = containers.Map({...\n"
        back += values
        back += "}, {\n"
        back += keys
        back += "});\n"

        ret += fwd + back
    return ret

def declarations(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(matlabFieldName(msg,field) + ";")
            if "Enum" in field:
                ret.append(matlabFieldName(msg,field) + "AsInt;")
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append(bits["Name"] + ";")
                    if "Enum" in bits:
                        ret.append(bits["Name"] + "AsInt;")
    return ret

def fieldDefault(field):
    if "Default" in field:
        return str(field["Default"])
    # should be based on type
    return "0"

def initField(msg, field):
    defaultValue = fieldType(field) + "("+ fieldDefault(field) +")"
    if MsgParser.fieldCount(field) > 1:
        ret =  "for index="+str(MsgParser.fieldCount(field))+": -1: 1\n"
        ret += "    obj." + matlabFieldName(msg,field) + "(index) = " + defaultValue + ";\n"
        ret += "end"
        return ret
    else:
        return  "obj." + matlabFieldName(msg,field) + " = " + defaultValue + ";"

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
            fieldInit = initField(msg, field)
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
                if "Enum" in field:
                    pass
                getStr = "obj."+matlabFieldName(msg,field)
                if "Enum" in field:
                    getStr += "AsInt"
                getStr = "uint32("+getStr+")"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        if "Enum" in bitfield:
                            pass
                        getStr = "obj."+BitfieldName(field, bitfield)
                        if "Enum" in bitfield:
                            getStr += "AsInt"
                        getStr = "uint32("+getStr+")"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nid = bitshift(id, -" + str(numBits)+")\n"
                numBits = field["IDBits"]
                setStr = "bitand(id, "+Mask(numBits)+")"
                #if "Enum" in field:
                #    setStr = field["Enum"]+"("+setStr+")"
                ret +=  "obj."+matlabFieldName(msg,field)+" = "+setStr
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = id >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "bitand(id, "+Mask(numBits)+")"
                        #if "Enum" in bitfield:
                        #    setStr = bitfield["Enum"]+"("+setStr+")"
                        ret +=  "obj."+bitfield["Name"]+" = "+setStr
    return ret

oneOutputFilePerMsg = True
