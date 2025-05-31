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

def cosmosType(t):
    ret = t
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
    try:
        min = field["Min"] if "Min" in field else "MIN"
        max = field["Max"] if "Max" in field else "MAX"
        count = MsgParser.fieldCount(field)
        name = field["Name"]
        default = fieldDefault(field)
        description = MsgParser.fieldDescription(field)
        if "Enum" in field:
            enumeration = field["Enum"]
        else:
            enumeration = None
        if "Units" in field and field["Units"] != "":
            units = field["Units"].strip()
        else:
            units = None
        if fieldHasConversion(field):
            scale, offset = scale_and_offset(field)
        else:
            scale = None
            offset = None
    except TypeError:
        # Don't set min/max for header fields to what's in the Python code
        # because the Python code generator calculates them based on field
        # size as the min/max expressable value, and that's useless clutter
        # in Cosmos dictionaries.
        min = None #field.minVal
        max = None #field.maxVal
        count = field.count
        name = field.name
        default = field.get.default
        description = field.description
        enumeration = None
        units = None
        scale = None
        offset = None
        if field.idbits > 0:
            prefix = prefix + "ID_"
    array_bitsize = bit_size * count
    if is_cmd:
        if count == 1:
            ret = '%sPARAMETER %s %d %d  %s %s %s %s "%s"' % (prefix, name, bit_location, bit_size, type, min, max, default, description)
        else:
            ret = '%sARRAY_PARAMETER %s %d %d %s %s "%s"' % (prefix, field["Name"], bit_location, bit_size, type, array_bitsize, description)
    else:
        if count == 1:
            ret = '%sITEM      %s %d %d  %s "%s"'  % (prefix, name, bit_location, bit_size, type, description)
        else:
            ret = '%sARRAY_ITEM      %s %d %d  %s %d "%s"'  % (prefix, name, bit_location, bit_size, type, array_bitsize, description)
        if min and max:
            # this is:
            # Limits Set name (DEFAULT is fine)
            # Persistence (how many violations before flagged, 1 is fine)
            # Initial State, either ENABLED or DISABLED
            # 4 required values: red low, yellow low, yellow high, red high
            # 2 optional values: green low, green high (not used)
            ret += "\n%s  LIMITS DEFAULT 1 ENABLED %s %s %s %s" % (prefix, min, min, max, max)
            
    if enumeration:
        if enumeration in msg_enums:
            enum = msg_enums[enumeration]
            for option in enum["Options"]:
                name = OptionName(option)
                value = str(option["Value"])
                ret += "%s  STATE %s %s" % (name, value)
    if units:
        ret += "\n  %sUNITS %s %s" % (prefix, units, units)
    if scale and offset:
        conversion = "POLY_WRITE_CONVERSION" if is_cmd else "POLY_READ_CONVERSION"
        ret += "\n  %s%s %s %s" % (prefix, conversion, str(offset), str(scale))
    return ret

def header_declarations(header, is_cmd):
    ret = []
    for field in header.fields:
        ret.append(generic_declaration("  ", is_cmd, field, cosmosType(field.type), 8*field.offset, 8*field.size, field.enum))
        if len(field.bitfieldInfo) > 0:
            bit_offset = 0
            for bitfield in field.bitfieldInfo:
                # This is a bad idea, but we're trying to calculate the number of bits based on the max value of the
                # bitfield.  It should work for unsigned integers, but it doesn't work if the bitfield has a scale factor
                # or offset for floating point conversion.  Unfortunately, the python bitfield info doesn't include
                # the number of bits or the bit offset.  If it did, we wouldn't need to do this math :(.
                import math
                num_bits = int(math.log2(1+int(bitfield.maxVal)))
                ret.append(generic_declaration("  ", is_cmd, bitfield, cosmosType(bitfield.type), 8*field.offset+bit_offset, num_bits, field.enum))
                bit_offset += num_bits
    return ret

def declarations(msg, msg_enums):
    if MsgParser.MessageHeader:
        field_base_location = MsgParser.MessageHeader.SIZE * 8
    else:
        field_base_location = 0
    ret = []
    ret += ['COMMAND TARGET_NAME <MSGFULLNAME> %s "<MSGDESCRIPTION>"' % (msgEndian(msg))]
    if MsgParser.MessageHeader:
        ret += header_declarations(MsgParser.MessageHeader, True)
    ret += [
        '',
        '  # Command Fields have:        PARAMETER        Name  BitOffset BitSize Type  Min Max  Default               Description',
        '  # Command Array Fields have:  ARRAY_PARAMETER  Name  BitOffset BitSize Type                   ArrayBitSize  Description']
    ret += specialized_declarations(True, msg, msg_enums, field_base_location)
    ret += ['','TELEMETRY TARGET_NAME <MSGFULLNAME> %s "<MSGDESCRIPTION>"' % (msgEndian(msg))]
    if MsgParser.MessageHeader:
        ret += header_declarations(MsgParser.MessageHeader, False)
    ret += [
        '',
        '  # Telemetry Fields have:       ITEM        Name  BitOffset BitSize Type               Description',
        '  # Telemetry Array Fields have: ARRAY_ITEM  Name  BitOffset BitSize Type  ArrayBitSize Description']
    ret += specialized_declarations(False, msg, msg_enums, field_base_location)
    return ret

def specialized_declarations(is_cmd, msg, msg_enums, field_base_location):
    ret = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            field_bit_location = field_base_location + 8 * MsgParser.fieldLocation(field)
            ret.append(generic_declaration("  ", is_cmd, field, cosmosType(field["Type"]), field_bit_location, 8*MsgParser.fieldSize(field), msg_enums))
            if "Bitfields" in field:
                ret.append("    OVERLAP")
                bitOffset = 0
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(generic_declaration("    ", is_cmd, bits, cosmosType(field["Type"]), field_bit_location+bitOffset, numBits, msg_enums))
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
