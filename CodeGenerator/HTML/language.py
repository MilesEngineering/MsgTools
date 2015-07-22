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

def createFieldInfoRow(field, messageName):
    name = str(field["Name"]) if "Name" in field else "n/a"
    fieldtype = str(field["Type"]) if "Type" in field else "n/a"
    count = str(field["Count"]) if "Count" in field else "1"
    units = str(field["Units"]) if "Units" in field else "n/a"

    if "Enum" in field:
        units = str(field["Enum"])

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

def initCode(msg):
    ret = []

    for field in msg["Fields"]:
        fieldInfoRow = createFieldInfoRow(field, msg["Name"])
        
        if fieldInfoRow:
            ret.append(fieldInfoRow)
        
        #if "Bitfields" in field:
        #    for bits in field["Bitfields"]:
        #        bits = createBitfieldInfo(field, bits, msg["Name"])
        #        if bits:    
        #            ret.append(bits)

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
