import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

import msgtools.parser.cpp.language as cpplanguage
import msgtools.parser.simulink.language as simlanguage

cpplanguage.namespace = "<MSGFULLNAME>_"
cpplanguage.firstParam = "m_data"
cpplanguage.firstParamDecl = "uint8_t* m_data"
cpplanguage.const = ""
cpplanguage.enumNamespace = 1
enumNamespace = 1
cpplanguage.functionPrefix = "INLINE "
cpplanguage.enumClass = ""

#enums = cpplanguage.enums
accessors = cpplanguage.accessors
#declarations = cpplanguage.declarations
#structPacking = cpplanguage.structPacking
#structUnpacking = cpplanguage.structUnpacking
initCode = cpplanguage.initCode
#get_fields = simlanguage.get_fields
#set_fields = simlanguage.set_fields

def enums(e):
    ret = ""
    for enum in e:
        ret +=  "typedef enum {\n"
        for option in enum["Options"]:
            optionName = OptionName(option)
            if enumNamespace != 0:
                optionName = "<MSGFULLNAME>"+"_"+enum["Name"] + "_" + optionName
            ret += "    " + optionName + " = "+str(option["Value"]) + ",\n"
        ret = ret[:-2] + "\n"
        ret += "} <MSGFULLNAME>" + "_" + enum["Name"] + ";\n"
    return ret

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
                        retType = "<MSGFULLNAME>" + "_" + bits["Enum"]
                    if MsgParser.fieldCount(field) == 1:
                        ret.append(retType + " " + bits["Name"] + ";")
                    else:
                        ret.append(retType + " " + bits["Name"] + "["+str(MsgParser.fieldCount(field))+"];")
            else:
                retType = cpplanguage.fieldType(field)
                if fieldHasConversion(field):
                    retType = typeForScaledInt(field)
                elif "Enum" in field:
                    retType = "<MSGFULLNAME>" + "_" + field["Enum"]
                if MsgParser.fieldCount(field) == 1:
                    ret.append(retType + " " + field["Name"] + ";")
                else:
                    ret.append(retType + " " + field["Name"] + "["+str(MsgParser.fieldCount(field))+"];")
    return ret


def set_field(msg, field, count):
    if "Enum" in field:
        enumCast = "(<MSGFULLNAME>Message" + "::" + field["Enum"] + ")"
    else:
        enumCast = ""

    if count == 1:
        ret = "msg->Set%s(%sunpackedMsg->%s);" % (field["Name"], enumCast, field["Name"])
    else:
        ret = ""
        for idx in range(count):
            ret = ret + "msg->Set%s(%sunpackedMsg->%s[%d], %d);\n" % (field["Name"], enumCast, field["Name"], idx, idx)
        ret = ret[:-1]
    return ret


def set_fields(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    ret.append(set_field(msg, bitfield, fieldCount(field)))
            else:
                ret.append(set_field(msg, field, fieldCount(field)))
    return ret

def get_field(msg, field, count):
    if "Enum" in field:
        enumCast = "(<MSGFULLNAME>" + "_" + field["Enum"] + ")"
    else:
        enumCast = ""

    if count == 1:
        ret = "unpackedMsg->%s = %smsg->Get%s();" % (field["Name"], enumCast, field["Name"])
    else:
        ret = ""
        for idx in range(count):
            ret = ret + "unpackedMsg->%s[%d] = %smsg->Get%s(%d);\n" % (field["Name"], idx, enumCast, field["Name"], idx)
        ret = ret[:-1]
    return ret


def get_fields(msg):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    ret.append(get_field(msg, bitfield, fieldCount(field)))
            else:
                ret.append(get_field(msg, field, fieldCount(field)))

    return ret
