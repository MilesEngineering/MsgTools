import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

import msgtools.parser.cpp.language as language

language.namespace = "<MSGNAME>_"
language.firstParam = "m_data"
language.firstParamDecl = "uint8_t* m_data"
language.const = ""
language.enumNamespace = 1
language.functionPrefix = "INLINE "
language.enumClass = ""

enums = language.enums
accessors = language.accessors
declarations = language.declarations
initCode = language.initCode

def fieldDefault(field):
    ret = field["Default"]
    if("Type" in field and "int" in field["Type"]) and ret > 2**31:
        ret = str(ret)+'u'
    return ret

def fieldInfo(field, offset):
    ret = ""
    if "Default" in field:
        ret += '#define <MSGNAME>_'+field["Name"]+'_DEFAULT ' + str(fieldDefault(field)) + "\n"
    if MsgParser.fieldCount(field) > 1:
        ret += '#define <MSGNAME>_'+field["Name"]+'_COUNT ' + str(MsgParser.fieldCount(field)) + "\n"
    ret += '#define <MSGNAME>_'+field["Name"]+'_OFFSET ' + str(offset) + "\n"
    ret += '#define <MSGNAME>_'+field["Name"]+'_SIZE ' + str(MsgParser.fieldSize(field)) + "\n"
    return ret

def fieldBitsInfo(field, bits, offset, bitOffset, numBits):
    ret = ""
    if "Default" in bits:
        ret += '#define <MSGNAME>_'+bits["Name"]+'_Default ' + str(bits["Default"]) + "\n"
    return ret

def fieldInfos(msg):
    ret = ""
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret += fieldInfo(field, offset)
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret += fieldBitsInfo(field, bits, offset, bitOffset, numBits)
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return ret

def getMsgID(msg):
    return baseGetMsgID("<MSGNAME>_", "m_data", "CAST_ALL", 0, msg)
    
def setMsgID(msg):
    return baseSetMsgID("<MSGNAME>_", "m_data, ", 0, 0, msg)
