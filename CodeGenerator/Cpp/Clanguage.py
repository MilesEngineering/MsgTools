import MsgParser
from MsgUtils import *

import language

language.namespace = "<MSGNAME>_"
language.firstParam = "m_data"
language.firstParamDecl = "uint8_t* m_data"
language.const = ""
language.enumNamespace = 1
language.functionPrefix = "extern inline "
language.enumClass = ""

enums = language.enums
accessors = language.accessors
declarations = language.declarations
initCode = language.initCode

def fieldInfo(field, offset):
    ret = ""
    if "Default" in field:
        ret += '#define <MSGNAME>_'+field["Name"]+'_Default ' + str(field["Default"]) + "\n"
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
