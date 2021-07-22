import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def outputSubdir(outDir, filename):
    return outDir + "/+" + filename

def fieldType(field):
    typeStr = field["Type"]
    if "int" in typeStr:
        return typeStr
    if typeStr == "float32":
        return "single";
    if typeStr == "float64":
        return "double";
    return "?"

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "single"

def set_field(msg, field):
    if fieldCount(field) == 1:
        ret = "<MSGFULLNAME>_Set%s(m_data, %s);" % (field["Name"], field["Name"])
    else:
        ret = '''\
for (int i=0; i < %d; i++)
{
    <MSGFULLNAME>_Set%s(m_data, %s[i], i);
}
''' % (fieldCount(field), field["Name"], field["Name"])
    return ret

def set_fields(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    ret.append(set_field(msg, bitfield))
            else:
                ret.append(set_field(msg, field))

    return ret

def get_field(msg, field):
    if fieldCount(field) == 1:
        ret = "%s = <MSGFULLNAME>_Get%s(m_data);" % (field["Name"], field["Name"])
    else:
        ret = '''\
for (int i=0; i < %d; i++)
{
    %s[i] = <MSGFULLNAME>_Get%s(m_data, i);
}
''' % (fieldCount(field), field["Name"], field["Name"])
    return ret

def get_fields(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    ret.append(get_field(msg, bitfield))
            else:
                ret.append(get_field(msg, field))

    return ret

def accessors(msg):
    return []

def enums(e):
    return ""

def declarations(msg):
    return []

def fieldDefault(field):
    return "0"

def initCode(msg):
    return []

def undefinedMsgId():
    return "-1"

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
