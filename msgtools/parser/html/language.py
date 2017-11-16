import msgtools.parser.parser as MsgParser

def accessors(msg):
    return ""

def createFieldInfoRow(field):
    name = str(field["Name"]) if "Name" in field else "ERROR"
    fieldtype = str(field["Type"]) if "Type" in field else "ERROR"
    count = str(field["Count"]) if "Count" in field else "1"

    units = str(field["Units"]) if "Units" in field else ""

    if "Enum" in field:
        units = str(field["Enum"])
    elif "Bitfields" in field:
        units = "Bitfield"

    scale = str(field["Scale"]) if "Scale" in field else ""
    offset = str(field["Offset"]) if "Offset" in field else ""
    default = str(field["Default"]) if "Default" in field else ""
    min = str(MsgParser.fieldMin(field))
    max = str(MsgParser.fieldMax(field))
    description = str(field["Description"]) if "Description" in field else ""

    html = "\
        <tr>\
            <td class='fieldname'>" + name + "</td>\
            <td class='fieldtype'>" + fieldtype + "</td>\
            <td class='fieldcount'>" + count + "</td>\
            <td class='fieldunits'>" + units + "</td>\
            <td class='fieldscale'>" + scale + "</td>\
            <td class='fieldoffset'>" + offset + "</td>\
            <td class='fielddefault'>" + default + "</td>\
            <td class='fielddefault'>" + min + " - " + max + "</td>\
            <td class='fielddescription'>" + description + "</td>\
        </tr>\
    "
    return html

def createBitfieldInfoRow(bitfield):
    name = "&nbsp&nbsp&nbsp&nbsp" + str(bitfield["Name"]) if "Name" in bitfield else "ERROR"
    bitfieldtype = str(bitfield["NumBits"]) + " bits" if "NumBits" in bitfield else "ERROR"
    count = str(bitfield["Count"]) if "Count" in bitfield else "1"
    units = str(bitfield["Units"]) if "Units" in bitfield else ""

    if "Enum" in bitfield:
        units = "<ENUM>" + str(bitfield["Enum"]) + "</ENUM>"

    scale = str(bitfield["Scale"]) if "Scale" in bitfield else ""
    offset = str(bitfield["Offset"]) if "Offset" in bitfield else ""
    default = str(bitfield["Default"]) if "Default" in bitfield else ""
    min = str(MsgParser.fieldMin(bitfield))
    max = str(MsgParser.fieldMax(bitfield))
    description = str(bitfield["Description"]) if "Description" in bitfield else ""

    html = "\
        <tr>\
            <td> <span style=\"font-size: 1.3em;\">&#x21e8;</span>" + name + " </td>\
            <td>" + bitfieldtype + "</td>\
            <td>" + count + "</td>\
            <td>" + units + "</td>\
            <td>" + scale + "</td>\
            <td>" + offset + "</td>\
            <td>" + default + "</td>\
            <td>" + min + " - " + max + "</td>\
            <td>" + description + "</td>\
        </tr>\
    "
    return html

def initCode(msg):
    ret = []

    if "Fields" in msg:
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
    html = []

    for enum in e:
        enum["Name"]

        options = []

        for option in enum["Options"]:
            options.append("<tr><td>" + str(option["Name"]) + "</td><td>" + str(option["Value"]) + "</td></tr>")

        html.append("<div class='row'>\
            <div class='col-lg-4'>\
                <table class='table table-bordered table-hover table-striped'>\
                    <caption>Enumeration: " + enum["Name"] + "</caption>\
                    <thead>\
                        <tr>\
                            <th>Option</th>\
                            <th>Value</th>\
                        </tr>\
                    </thead>\
                    " + "\n".join(options) + "\
                </table>\
            </div>\
        </div>")

    return "\n".join(html)

def declarations(msg):
    return [""]
