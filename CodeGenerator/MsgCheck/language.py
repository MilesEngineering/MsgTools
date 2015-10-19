import MsgParser
import sys

# >/</= means big/little/native endian, see docs for struct.pack_into or struct.unpack_from.
def fieldType(field):
    allowedFieldTypes = \
    ["uint64", "uint32", "uint16", "uint8",
      "int64",  "int32",  "int16",  "int8",
      "float64", "float32"]
    return field["Type"] in allowedFieldTypes

def msgSize(msg):
    offset = 0
    for field in msg["Fields"]:
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)
    return offset

def fnHdr(field, count, name):
    param = "message_buffer"
    if str.find(name, "Set") == 0:
        param += ", value"
    if  count > 1:
        param += ", idx"
    ret = '''\
@staticmethod
@msg.units('%s')
@msg.default('%s')
@msg.count(%s)
def %s(%s):
    """%s"""''' % (MsgParser.fieldUnits(field), str(MsgParser.fieldDefault(field)), str(count), name, param, MsgParser.fieldDescription(field))
    return ret

def enumLookup(msg, field):
    lookup  = "defaultValue = 0\n"
    lookup += "    if isinstance(value, int) or value.isdigit():\n"
    lookup += "        defaultValue = int(value)\n"
    lookup += "    value = " + msg["Name"] + "." + str(field["Enum"]) + ".get(value, defaultValue)\n"
    lookup += "    "
    return lookup

def accessors(msg):
    offset = 0
    for field in msg["Fields"]:
        bitOffset = 0
        if "Enum" in field:
            #if not field["Enum"] in allowedEnums:
            #    sys.stderr.write('bad enum')
            #    sys.exit(1)
            pass
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                bitOffset += numBits
            if bitOffset > 8*MsgParser.fieldSize(field):
                sys.stderr.write('too many bits')
                sys.exit(1)
            if "Enum" in bits:
                #global allowedEnums
                #if not bits["Enum"] in allowedEnums:
                #    sys.stderr.write('bad enum')
                pass
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)
    
    if offset > 256:
        sys.stderr.write('message too big')

    return ""

def declarations(msg):
    return [""]

def initCode(msg):
    return []
