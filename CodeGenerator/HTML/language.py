import MsgParser

def msgSize(msg):
    offset = 0
    for field in msg["Fields"]:
        offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)
    return offset

def reflection(msg):
    return ""

def accessors(msg):
    return ""

def createFieldInfoRow(field):
    name = str(field["Name"]) if "Name" in field else "ERROR"
    fieldtype = str(field["Type"]) if "Type" in field else "ERROR"
    count = str(field["Count"]) if "Count" in field else "1"

    units = str(field["Units"]) if "Units" in field else "n/a"

    if "Enum" in field:
        units = str(field["Enum"])
    elif "Bitfields" in field:
        units = "Bitfield"

    scale = str(field["Scale"]) if "Scale" in field else "n/a"
    offset = str(field["Offset"]) if "Offset" in field else "n/a"
    description = str(field["Description"]) if "Description" in field else "n/a"

    html = "\
        <tr>\
            <td>" + name + "</td>\
            <td>" + fieldtype + "</td>\
            <td>" + count + "</td>\
            <td>" + units + "</td>\
            <td>" + scale + "</td>\
            <td>" + offset + "</td>\
            <td>" + description + "</td>\
        </tr>\
    "
    return html

def createBitfieldInfoRow(bitfield):
    name = "&nbsp&nbsp&nbsp&nbsp" + str(bitfield["Name"]) if "Name" in bitfield else "ERROR"
    bitfieldtype = str(bitfield["NumBits"]) + " bits" if "NumBits" in bitfield else "ERROR"
    count = str(bitfield["Count"]) if "Count" in bitfield else "1"
    units = str(bitfield["Units"]) if "Units" in bitfield else "n/a"

    if "Enum" in bitfield:
        units = str(bitfield["Enum"])

    scale = str(bitfield["Scale"]) if "Scale" in bitfield else "n/a"
    offset = str(bitfield["Offset"]) if "Offset" in bitfield else "n/a"
    description = str(bitfield["Description"]) if "Description" in bitfield else "n/a"

    html = "\
        <tr>\
            <td>" + name + "</td>\
            <td>" + bitfieldtype + "</td>\
            <td>" + count + "</td>\
            <td>" + units + "</td>\
            <td>" + scale + "</td>\
            <td>" + offset + "</td>\
            <td>" + description + "</td>\
        </tr>\
    "
    return html


def initCode(msg):
    ret = []

    for field in msg["Fields"]:
        fieldInfoRow = createFieldInfoRow(field)
        
        if fieldInfoRow:
            ret.append(fieldInfoRow)
        
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                bits_html = createBitfieldInfoRow(bits)
                if bits:    
                    ret.append(bits_html)

    return ret

def enums(e):
    ret = ""
    for enum in e:
        # forward enum
        fwd = enum["Name"]+" = {"
        for option in enum["Options"]:
            fwd += '"'+option["Name"]+'"'+" : "+str(option["Value"]) + ', '
        fwd = fwd[:-2]
        fwd += "}\n"

        # Reverse enum
        back = "Reverse" + enum["Name"]+" = {"
        for option in enum["Options"]:
            back += str(option["Value"]) +' : "'+str(option["Name"]) + '", '
        back = back[:-2]
        back += "}\n"

        ret += fwd + back
    return ret
