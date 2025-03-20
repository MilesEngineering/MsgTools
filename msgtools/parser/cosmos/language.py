import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *
    
def accessors(msg):
    return []

def fieldDefault(field, as_enum=False):
    try:
        ret = field["Default"]
    except KeyError:
        ret = 0
    return ret

def enums(e):
    ret = ""
    for enum in e:
        ret +=  "enum " + enum["Name"]+" {"
        for option in enum["Options"]:
            optionName = OptionName(option)
            ret += optionName+" = "+str(option["Value"]) + ', '
        ret = ret[:-2]
        ret += "};\n"
    return ret

def cosmosType(field):
    ret = field["Type"]
    if ret.startswith("float"):
        ret = "FLOAT"
    elif ret.startswith("int"):
        ret = "INT"
    elif ret.startswith("uint"):
        ret = "UINT"
    return ret

def fieldInfos(msg):
    return ""

def scale_and_offset(field):
    scale = 1.0
    offset = 0.0
    if "Scale" in field:
        scale = field["Scale"]
    if "Offset" in field:
        offset = field["Offset"]
    return (scale, offset)

def generic_declaration(prefix, is_cmd, field, type, bit_location, bit_size, msg_enums):
    ret = ""
    min = field["Min"] if "Min" in field else "MIN"
    max = field["Max"] if "Max" in field else "MAX"
    count = MsgParser.fieldCount(field)
    array_bitsize = bit_size * count
    if is_cmd:
        if count == 1:
            ret = '%sPARAMETER %s %d %d  %s %s %s %s "%s"' % (prefix, field["Name"], bit_location, bit_size, type, min, max, fieldDefault(field), MsgParser.fieldDescription(field))
        else:
            ret = '%sARRAY_PARAMETER %s %d %d %s %s "%s"' % (prefix, field["Name"], bit_location, bit_size, type, array_bitsize, MsgParser.fieldDescription(field))
    else:
        if count == 1:
            ret = '%sITEM      %s %d %d  %s "%s"'  % (prefix, field["Name"], bit_location, bit_size, type, MsgParser.fieldDescription(field))
        else:
            ret = '%sARRAY_ITEM      %s %d %d  %s %d "%s"'  % (prefix, field["Name"], bit_location, bit_size, type, array_bitsize, MsgParser.fieldDescription(field))
        if "Min" in field or "Max" in field:
            # this is:
            # Limits Set name (DEFAULT is fine)
            # Persistence (how many violations before flagged, 1 is fine)
            # Initial State, either ENABLED or DISABLED
            # 4 required values: red low, yellow low, yellow high, red high
            # 2 optional values: green low, green high (not used)
            ret += "\n%s  LIMITS DEFAULT 1 ENABLED %s %s %s %s" % (prefix, min, min, max, max)
            
    if "Enum" in field:
        if field["Enum"] in msg_enums:
            enum = msg_enums[field["Enum"]]
            for option in enum["Options"]:
                name = OptionName(option)
                value = str(option["Value"])
                ret += "%s  STATE %s %s" % (name, value)
    if "Units" in field and field["Units"] != "":
        ret += "\n  %sUNITS %s %s" % (prefix, field["Units"].strip(), field["Units"].strip())
    if fieldHasConversion(field):
        conversion = "POLY_WRITE_CONVERSION" if is_cmd else "POLY_READ_CONVERSION"
        scale, offset = scale_and_offset(field)
        ret += "\n  %s%s %s %s" % (prefix, conversion, str(offset), str(scale))
    return ret

def declarations(msg, msg_enums):
    field_base_location = 32
    ret = []
    ret += [
        'COMMAND TARGET_NAME <MSGFULLNAME> %s "<MSGDESCRIPTION>"' % (msgEndian(msg)),
        '  ID_PARAMETER MESSAGE_ID  0  %d   UINT    <MSGID>  "Message ID"' % (field_base_location),
        '',
        '  # Fields have:        PARAMETER        Name  BitOffset BitSize Type  Min Max  Default               Description',
        '  # Array Fields have:  ARRAY_PARAMETER  Name  BitOffset BitSize Type                   ArrayBitSize  Description']
    ret += specialized_declarations(True, msg, msg_enums, field_base_location)
    ret += [
        '',
        'TELEMETRY TARGET_NAME <MSGFULLNAME> %s "<MSGDESCRIPTION>"' % (msgEndian(msg)),
        '  ID_ITEM MESSAGE_ID  0  %d   UINT    <MSGID>  "Message ID"' % (field_base_location),
        '',
        '  # Fields have:       ITEM        Name  BitOffset BitSize Type               Description',
        '  # Array Fields have: ARRAY_ITEM  Name  BitOffset BitSize Type  ArrayBitSize Description']
    ret += specialized_declarations(False, msg, msg_enums, field_base_location)
    return ret

def specialized_declarations(is_cmd, msg, msg_enums, field_base_location):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            field_bit_location = field_base_location + 8 * MsgParser.fieldLocation(field)
            ret.append(generic_declaration("  ", is_cmd, field, cosmosType(field), field_bit_location, 8*MsgParser.fieldSize(field), msg_enums))
            if "Bitfields" in field:
                ret.append("    OVERLAP")
                bitOffset = 0
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(generic_declaration("    ", is_cmd, bits, cosmosType(field), field_bit_location+bitOffset, numBits, msg_enums))
                    ret.append("      OVERLAP")
                    bitOffset += numBits
    return ret

def msgEndian(msg):
    return "BIG_ENDIAN" if MsgParser.big_endian else "LITTLE_ENDIAN"

def getMsgID(msg):
    return baseGetMsgID("", "", "CAST_ENUMS", 0, msg)
    
def setMsgID(msg):
    return baseSetMsgID("", "", 1, 0, msg)

def initCode(msg):
    return []
