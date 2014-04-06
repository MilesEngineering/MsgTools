import MsgParser

def fieldType(field):
    return field["Type"] + "_t"

def getFn(field, offset):
    return fieldType(field) + " Get" + field["Name"] + "() { return *("+fieldType(field)+"*)&m_data["+str(offset)+"]; }\n"

def setFn(field, offset):
    return "void Set" + field["Name"] + "(" + fieldType(field) + "& value) { *("+fieldType(field)+"*)&m_data["+str(offset)+"] = value; }\n"

def accessors(msg):
    gets = ""
    sets = ""
    
    offset = 0
    for field in msg["Fields"]:
        gets += getFn(field, offset)
        sets += setFn(field, offset)
        offset += MsgParser.fieldSize(field)

    return gets+sets
