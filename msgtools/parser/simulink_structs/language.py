import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

import msgtools.parser.cpp.language as language

#language.namespace = "<MSGFULLNAME>_"
#language.firstParam = "m_data"
#language.firstParamDecl = "uint8_t* m_data"
#language.const = ""
language.enumNamespace = 1
#language.functionPrefix = "INLINE "
language.enumClass = ""

enums = language.enums
accessors = language.accessors
#declarations = language.declarations
structPacking = language.structPacking
structUnpacking = language.structUnpacking
initCode = language.initCode

def declarations(msg, msg_enums):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    retType = language.fieldType(field)
                    if fieldHasConversion(bits):
                        retType = typeForScaledInt(bits)
                    elif "Enum" in bits:
                        retType = "enum "+bits["Enum"]
                    ret.append(retType + " " + bits["Name"] + ";")
            else:
                retType = language.fieldType(field)
                if fieldHasConversion(field):
                    retType = typeForScaledInt(field)
                elif "Enum" in field:
                    retType = "enum "+field["Enum"]
                if MsgParser.fieldCount(field) == 1:
                    ret.append(retType + " " + field["Name"] + ";")
                else:
                    ret.append(retType + " " + field["Name"] + "["+str(MsgParser.fieldCount(field))+"];")
    return ret
