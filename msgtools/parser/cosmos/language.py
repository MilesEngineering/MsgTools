from typing import List
import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

    
class IndentationManager:
    _indentation = ""

    def __init__(self, additional_numspaces: int = None):
        self.numspaces = additional_numspaces

    def __enter__(self):
        if self.numspaces:
            IndentationManager._indentation += " " * self.numspaces
        return IndentationManager._indentation

    def __exit__(self, exc_type, exc_val, exc_tb):
        IndentationManager._indentation = IndentationManager._indentation[:-self.numspaces]



class BitfieldElement:
    """This is an element of a bitfield structure"""
    def __init__(self, num_bits: int, name: str, element_type: str, endianness: str, description: str, default, min=None, max=None):
        self.num_bits = num_bits
        self.name = name
        self.type = element_type
        self.endianness = endianness
        self.description = description
        self.min = "MIN" if not min else min
        self.max = "MAX" if not max else max
        self.default = default

    def write(self, tmtc: str, bit_location: int) -> str:
        # we shall consider to add also units. In my opinion this module shall be refactored anyway, so I'll
        # leave it like this for now
        with IndentationManager(2) as prefix:
            if tmtc == "ITEM":
                out = f'{prefix}ITEM      {self.name} {bit_location} {self.num_bits} {cosmosType(self.type)} "{self.description}" {self.endianness}'
            elif tmtc == "PARAMETER":
                out = f'{prefix}PARAMETER      {self.name} {bit_location} {self.num_bits} {cosmosType(self.type)} {self.min} {self.max} {self.default} "{self.description}" {self.endianness}'
        return out
    
class LittleEndianBitfieldStructure:
    """
    This class holds all the information of a bitfield whose code has to be generated in little endian manner. 
    Description of how these type of bitfields have to be managed in Cosmos syntax can be found 
    [here](https://docs.openc3.com/docs/guides/little-endian-bitfields).
    """
    def __init__(self, tmtc: str, base_offset_bytes: int):
        """
        `base_offset_bytes` is the offset in bytes of the full structure in the message
        """
        self.allfields: List[BitfieldElement] = []
        self.base_offset_bit = base_offset_bytes * 8
        self.tmtc = tmtc
    
    def _get_bitpos_at_nextbyte(self, num_bits: int) -> int:
        """Private function, it takes a number of bits and returns the starting bit index of the next byte"""
        return (num_bits // 8 + 1) * 8

    def add_field(self, field: BitfieldElement):
        self.allfields.append(field)
    
    def write(self) -> str:
        out: List[str] = []
        offset = self.base_offset_bit

        for field in self.allfields:
            next_bit_location = self._get_bitpos_at_nextbyte(field.num_bits) - field.num_bits
            bit_location = offset + next_bit_location
            offset += next_bit_location
            out.append(field.write(self.tmtc, bit_location))

        return out



def accessors(msg):
    return []

def fieldDefault(field, as_enum=False):
    try:
        ret = field["Default"]
    except Exception:
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
        min = field.minVal
        max = field.maxVal
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
    
    # cosmos doesn't accept DBL_MIN and DBL_MAX 
    if min == "DBL_MIN":
        min = "MIN"
    if max == "DBL_MAX":
        max = "MAX"

    array_bitsize = bit_size * count
    if is_cmd:
        if count == 1:
            ret = '%sPARAMETER %s %d %d  %s %s %s %s "%s"' % (prefix, name, bit_location, bit_size, type, min, max, default, description)
        else:
            ret = '%sARRAY_PARAMETER %s %d %d %s %s "%s"' % (prefix, field["Name"], bit_location, bit_size, type, array_bitsize, description)
    else:
        if count == 1:
            if prefix.startswith("  ID_"):
                # ID_ITEMs want one more field than ITEM (https://docs.openc3.com/docs/configuration/telemetry#id_item). 
                # min and max shall be equal here, since this is a ITEM ID
                if min == max:
                    id_value = min
                else: 
                    raise Exception(f"min/max value are not equal for ID_ITEM {name}")
                ret = '%sITEM      %s %d %d  %s %d "%s"'  % (prefix, name, bit_location, bit_size, type, id_value, description)
            else:
                ret = '%sITEM      %s %d %d  %s "%s"'  % (prefix, name, bit_location, bit_size, type, description)
        else:
            ret = '%sARRAY_ITEM      %s %d %d  %s %d "%s"'  % (prefix, name, bit_location, bit_size, type, array_bitsize, description)
        
        if prefix.endswith("ID_"):
            prefix = "  "
        else:
            if min and max:
                # this is:
                # Limits Set name (DEFAULT is fine)
                # Persistence (how many violations before flagged, 1 is fine)
                # Initial State, either ENABLED or DISABLED
                # 4 required values: red low, yellow low, yellow high, red high
                # 2 optional values: green low, green high (not used)
                #
                # Also, here we have to avoid the case in which `prefix` contains "ID_"
                # so that we don't have an "ID_  LIMITS DEFAULT ..."
                if min != "MIN" and max != "MAX":
                    ret += "\n%s  LIMITS DEFAULT 1 ENABLED %s %s %s %s" % (prefix, min, min, max, max)
                elif type == "FLOAT" and bit_size == 64:
                    ret += "\n%s  LIMITS DEFAULT 1 ENABLED %s %s %s %s" % (prefix, "-1.7976931348623157e+308", "-1.7976931348623157e+308", "1.7976931348623157e+308", "1.7976931348623157e+308")
                elif type == "FLOAT" and bit_size == 32:
                    ret += "\n%s  LIMITS DEFAULT 1 ENABLED %s %s %s %s" % (prefix, "-3.402823e+38", "-3.402823e+38", "3.402823e+38", "3.402823e+38")
            
    if enumeration:
        if enumeration in msg_enums:
            enum = msg_enums[enumeration]
            for option in enum["Options"]:
                name = OptionName(option)
                value = str(option["Value"])
                ret += "%s  STATE %s %s" % (name, value)
    if units:
        ret += "\n  %sUNITS %s %s" % (prefix, units, units)
    if scale != None or offset != None:
        conversion = "POLY_WRITE_CONVERSION" if is_cmd else "POLY_READ_CONVERSION"
        ret += "\n  %s%s %s %s" % (prefix, conversion, str(offset), str(scale))
    return ret

def header_declarations(header, msg, is_cmd):
    ret = []
    for field in header.fields:
        if len(field.bitfieldInfo) > 0:
            if MsgParser.big_endian:
                bit_offset = 0
                for bitfield in field.bitfieldInfo:
                    num_bits = bitfield_size(bitfield)
                    with IndentationManager(2) as prefix:
                        ret.append(generic_declaration(msg, prefix, is_cmd, bitfield, cosmosType(bitfield.type), 8*field.offset+bit_offset, num_bits, field.enum))
                    bit_offset += num_bits
            else:
                tmtc = "PARAMETER" if is_cmd else "ITEM"
                little_endian_struct = LittleEndianBitfieldStructure(tmtc, field.offset)
                for bitfield in field.bitfieldInfo:
                    num_bits = bitfield_size(bitfield)
                    element = BitfieldElement(num_bits, bitfield.name, bitfield.type, "LITTLE_ENDIAN", bitfield.description, fieldDefault(bitfield), bitfield.minVal, bitfield.maxVal)
                    little_endian_struct.add_field(element)
                ret += little_endian_struct.write() # merge the lists
        else:
            with IndentationManager(2) as prefix:
                ret.append(generic_declaration(msg, prefix, is_cmd, field, cosmosType(field.type), 8*field.offset, 8*field.size, field.enum))
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
        with IndentationManager(2) as prefix:
            for field in msg["Fields"]:
                field_bit_location = field_base_location + 8 * MsgParser.fieldLocation(field)
                if "Bitfields" not in field:
                    ret.append(generic_declaration(msg, prefix, is_cmd, field, cosmosType(field["Type"]), field_bit_location, 8*MsgParser.fieldSize(field), msg_enums))

                else:
                    if MsgParser.big_endian:
                        bitOffset = 0
                        for bits in field["Bitfields"]:
                            numBits = bits["NumBits"]
                            with IndentationManager(4) as prefix:
                                ret.append(generic_declaration(msg, prefix, is_cmd, bits, cosmosType(field["Type"]), field_bit_location+bitOffset, numBits, msg_enums))
                            bitOffset += numBits
                    else: # little endian case
                        tmtc = "PARAMETER" if is_cmd else "ITEM"
                        little_endian_struct = LittleEndianBitfieldStructure(tmtc, field_bit_location)
                        for a_field in field["Bitfields"]:
                            description = ""
                            min = None 
                            max = None 
                            if "Description" in a_field:
                                description = a_field["Description"]
                            if "Min" in a_field:
                                min = a_field["Min"]
                            if "Max" in a_field:
                                min = a_field["Max"]

                            element = BitfieldElement(a_field["NumBits"], a_field["Name"], a_field["parent_field_type"], "LITTLE_ENDIAN", description, fieldDefault(a_field), min, max)
                            little_endian_struct.add_field(element)

                        ret += little_endian_struct.write()


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
