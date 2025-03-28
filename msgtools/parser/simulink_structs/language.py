import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

import msgtools.parser.cpp.language as cpplanguage
import msgtools.parser.simulink.language as simlanguage

cpplanguage.namespace = "<MSGFULLNAME>_"
cpplanguage.firstParam = "m_data"
cpplanguage.firstParamDecl = "uint8_t* m_data"
cpplanguage.const = ""
cpplanguage.enumNamespace = 1
cpplanguage.functionPrefix = "INLINE "
cpplanguage.enumClass = ""

enums = cpplanguage.enums
accessors = cpplanguage.accessors
#declarations = cpplanguage.declarations
#structPacking = cpplanguage.structPacking
#structUnpacking = cpplanguage.structUnpacking
initCode = cpplanguage.initCode
#get_fields = simlanguage.get_fields
#set_fields = simlanguage.set_fields


def declarations(msg, msg_enums):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    retType = cpplanguage.fieldType(field)
                    if fieldHasConversion(bits):
                        retType = typeForScaledInt(bits)
                    elif "Enum" in bits:
                        retType = "enum "+bits["Enum"]
                    ret.append(retType + " " + bits["Name"] + ";")
            else:
                retType = cpplanguage.fieldType(field)
                if fieldHasConversion(field):
                    retType = typeForScaledInt(field)
                elif "Enum" in field:
                    retType = "enum "+field["Enum"]
                if MsgParser.fieldCount(field) == 1:
                    ret.append(retType + " " + field["Name"] + ";")
                else:
                    ret.append(retType + " " + field["Name"] + "["+str(MsgParser.fieldCount(field))+"];")
    return ret


def set_field(msg, field):
    if fieldCount(field) == 1:
        ret = "<MSGFULLNAME>_Set%s(data, %s);" % (field["Name"], "unpackedMsg->" + field["Name"])
    else:
        ret = '''\
for (int i=0; i < %d; i++)
{
    <MSGFULLNAME>_Set%s(data, %s[i], i);
}
''' % (fieldCount(field), field["Name"], "unpackedMsg->" + field["Name"])
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
        ret = "%s = <MSGFULLNAME>_Get%s(data);" % ("unpackedMsg->" + field["Name"], field["Name"])
    else:
        ret = '''\
for (int i=0; i < %d; i++)
{
    %s[i] = <MSGFULLNAME>_Get%s(data, i);
}
''' % (fieldCount(field), "unpackedMsg->" + field["Name"], field["Name"])
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
