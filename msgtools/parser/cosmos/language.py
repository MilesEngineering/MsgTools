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

def generic_declaration(msg, prefix, is_cmd, field, type, bit_location, bit_size, msg_enums):
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
        # For any field that has ID bits, we ought to set the min, max, and default value all
        # to what the message definition says they should be.
        if field.idbits > 0:
            prefix = prefix + "ID_"
            # Currently we're only setting them for a field named "ID"!
            if name == "ID":
                default = msg["ID"]
                min = default
                max = default
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

def header_declarations(header, msg, is_cmd):
    ret = []
    for field in header.fields:
        ret.append(generic_declaration(msg, "  ", is_cmd, field, cosmosType(field.type), 8*field.offset, 8*field.size, field.enum))
        if len(field.bitfieldInfo) > 0:
            bit_offset = 0
            for bitfield in field.bitfieldInfo:
                num_bits = bitfield_size(bitfield)
                ret.append(generic_declaration(msg, "  ", is_cmd, bitfield, cosmosType(bitfield.type), 8*field.offset+bit_offset, num_bits, field.enum))
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
        ret += header_declarations(MsgParser.MessageHeader, msg, True)
    ret += [
        '',
        '  # Command Fields have:        PARAMETER        Name  BitOffset BitSize Type  Min Max  Default               Description',
        '  # Command Array Fields have:  ARRAY_PARAMETER  Name  BitOffset BitSize Type                   ArrayBitSize  Description']
    ret += specialized_declarations(True, msg, msg_enums, field_base_location)
    ret += ['','TELEMETRY TARGET_NAME <MSGFULLNAME> %s "<MSGDESCRIPTION>"' % (msgEndian(msg))]
    if MsgParser.MessageHeader:
        ret += header_declarations(MsgParser.MessageHeader, msg, False)
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
            ret.append(generic_declaration(msg, "  ", is_cmd, field, cosmosType(field["Type"]), field_bit_location, 8*MsgParser.fieldSize(field), msg_enums))
            if "Bitfields" in field:
                ret.append("    OVERLAP")
                bitOffset = 0
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(generic_declaration(msg, "    ", is_cmd, bits, cosmosType(field["Type"]), field_bit_location+bitOffset, numBits, msg_enums))
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

def bitfield_size(bitfield):
    # This is a bad idea, but we're trying to calculate the number of bits based on the max value of the
    # bitfield.  It should work for unsigned integers, but it doesn't work if the bitfield has a scale factor
    # or offset for floating point conversion.  Unfortunately, the python bitfield info doesn't include
    # the number of bits or the bit offset.  If it did, we wouldn't need to do this math :(.
    import math
    num_bits = int(math.log2(1+int(bitfield.maxVal)))
    return num_bits

def msgtools_connection(msg):
    msg_name = msg["Name"]
    length_field_offset_bits = None
    length_field_size_bits = None
    if "Fields" in msg:
        for field in msg["Fields"]:
            if field["Name"] == "DataLength":
                length_field_offset_bits = 8 * MsgParser.fieldLocation(field)
                length_field_size_bits = 8 * MsgParser.fieldSize(field)
            if "Bitfields" in field:
                bitOffset = 0
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    if bits["Name"] == "DataLength":
                        length_field_offset_bits = 8 * MsgParser.fieldLocation(field) + bitOffset
                        length_field_size_bits = numBits
                    bitOffset += numBits
    
    if length_field_offset_bits == None or length_field_size_bits == None:
        return "# Invalid header for Cosmos connection, no DataLength field."

    interface = [
    "INTERFACE",
    "MSGTOOLS_%s_INTERFACE" % (msg_name.upper().replace("HEADER", "")),
    # The type of Interface (TCP/IP Server or Client, or Serial, or UDP, or MQTT, or something else)
    "openc3/interfaces/tcpip_client_interface.py", # or openc3/interfaces/tcpip_server_interface.py
    # The IP address to connect to (perhaps localhost by default)
    "127.0.0.1",
    # msgserver uses port 5678 by default for TCP/IP, and the same port is used to send and receive.
    "5678 5678",
    # write timeout in seconds
    "10.0",
    # read timeout in seconds (Nil / None to block on read)
    "None",
    # Protocol = LENGTH
    "LENGTH",
    # Length Bit Offset.  This needs to be the location in bits from the start of the header where the length field is
    "%d" % (length_field_offset_bits),
    # Length Bit Size.  The size in bits of the length field.
    "%d" % (length_field_size_bits),
    # Length Value Offset.  Value to add to the length field (zero for interoperating with msgtools on TCP/IP)
    "0",
    # Bytes per Count.  1 for interoperating with msgtools on TCP/IP.
    "1",
    # Length Endianness.
    "BIG_ENDIAN",
    # Discard Leading Bytes.  zero for interoperating with msgtools on TCP/IP
    "0",
    # Sync Pattern.  Left blank or Nil/None for interoperating with msgtools on TCP/IP
    "None",
    # Max Length.  Could be inferred from number of bits of length field, but can leave blank or nil for interoperating with msgtools on TCP/IP
    "None",
    # Fill Length and Sync Pattern.  Must be True for interoperating with msgtools on TCP/IP.
    "True"
    ]
    interface_line = " ".join(interface)
    ret = "# Cosmos msgtools interface using %s and %s\n" % (msg_name, __file__)
    ret += '''
# Cosmos needs an Interface defined, with a Protocol:
#     https://docs.openc3.com/docs/configuration/interfaces
#     https://docs.openc3.com/docs/configuration/protocols
#
# For network communications, Cosmos can use a TCP/IP Server or Client:
#     https://docs.openc3.com/docs/configuration/interfaces#tcpip-server-interface
#     https://docs.openc3.com/docs/configuration/interfaces#tcpip-client-interface
#     If we have msgserver handle all I/O with the hardware, it'd make sense to have Cosmos
#     connect to msgserver using a TCP/IP Client connection!
#
# To interoperate with msgtools' msgserver or client applications, the "LENGTH" Protocol should be used in Cosmos.
#     https://docs.openc3.com/docs/configuration/protocols#length-protocol
#
# If we're going to use a TCP/IP client and LENGTH Protocol, there's still some decisions to be made.
# To autogenerate the INTERFACE line for use with this header, we'd need to specify:
# 1) The type of Interface (TCP/IP Server or Client, or Serial, or UDP, or MQTT, or something else)
# 2) The IP address to connect to (perhaps localhost by default)
# 3&4) msgserver uses port 5678 by default for TCP/IP, and the same port is used to send and receive.
# 5) write timeout in seconds
# 6) read timeout in seconds (Nil / None to block on read)
# 7) Protocol = LENGTH
# 8) Length Bit Offset.  This needs to be the location in bits from the start of the header where the length field is
# 9) Length Bit Size.  The size in bits of the length field.
# 10) Length Value Offset.  Value to add to the length field (zero for interoperating with msgtools on TCP/IP)
# 11) Bytes per Count.  1 for interoperating with msgtools on TCP/IP.
# 12) Length Endianness.
# 13) Discard Leading Bytes.  zero for interoperating with msgtools on TCP/IP
# 14) Sync Pattern.  Left blank or Nil/None for interoperating with msgtools on TCP/IP
# 15) Max Length.  Could be inferred from number of bits of length field, but can leave blank or nil for interoperating with msgtools on TCP/IP
# 16) Fill Length and Sync Pattern.  Must be True for interoperating with msgtools on TCP/IP.
'''
    ret += interface_line
    ret += "\n"
    return ret
