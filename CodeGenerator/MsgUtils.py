import re

def fieldSize(field):
    fieldSizes = {"uint64":8, "uint32":4, "uint16": 2, "uint8": 1, "int64":8, "int32":4, "int16": 2, "int8": 1, "float64":8, "float32":4}
    return fieldSizes[str.lower(field["Type"])]

def fieldIsInt(field):
    isInt  = 0
    if "Type" in field or "NumBits" in field:
        isInt = 1
    if "Type" in field and "int" in str.lower(field["Type"]):
        isInt = 1
    return isInt

def fieldNumBits(field):
    numBits = 0
    if "Type" in field or "NumBits" in field:
        numBits = fieldItem(field, "NumBits", 0)
    if "Type" in field:
        fieldType = str.lower(field["Type"])
        if "int" in fieldType:
            numBits = fieldSize(field) * 8
            if fieldType.startswith("int"):
                isSigned = 1
    return numBits

def fieldIsSigned(field):
    isSigned = 0
    if "Type" in field:
        fieldType = str.lower(field["Type"])
        if "int" in fieldType:
            if fieldType.startswith("int"):
                isSigned = 1
    return isSigned

def transformInt(field, value):
    if "Scale" in field or "Offset" in field:
        scale = fieldItem(field, "Scale", 1.0)
        offset = fieldItem(field, "Offset", 0.0)
        value = value * scale + offset
    return value

def fieldMin(field):
    if fieldIsInt(field):
        numBits = fieldNumBits(field)
        if fieldIsSigned(field):
            minVal = -2**(numBits-1)
        else:
            minVal = 0
        minVal = transformInt(field, minVal)
    minVal = fieldItem(field, "Min", minVal)
    return minVal

def fieldMax(field):
    if fieldIsInt(field):
        numBits = fieldNumBits(field)
        if fieldIsSigned(field):
            maxVal = 2**(numBits-1)-1
        else:
            maxVal = 2**numBits-1
        maxVal = transformInt(field, maxVal)
    maxVal = fieldItem(field, "Max", maxVal)
    return maxVal

def fieldItem(field, item, default):
    if item in field:
        return field[item]
    else:
        return default

def fieldUnits(field):
    return fieldItem(field, "Units", "")

def fieldDescription(field):
    return fieldItem(field, "Description", "")

def fieldDefault(field):
    return fieldItem(field, "Default", "")

def fieldCount(field):
    return fieldItem(field, "Count", 1)

def numberOfFields(msg):
    count = 0
    for field in msg["Fields"]:
        count+=1
        if "Bitfields" in field:
            for bitfield in field["Bitfields"]:
                count+=1
    return count    

def fieldReplacements(line,msg):
    line = re.sub('<FOREACHFIELD\(', '', line)
    line = re.sub('\)>$', '', line)
    ret = ""
    count = 0
    for field in msg["Fields"]:
        thisLine = line
        thisLine = thisLine.replace("<FIELDNAME>", field["Name"])
        thisLine = thisLine.replace("<FIELDNUMBER>", str(count))
        thisLine = thisLine.replace("<FIELDCOUNT>", str(fieldCount(field)))
        ret +=  thisLine
        count+=1
        if "Bitfields" in field:
            for bitfield in field["Bitfields"]:
                thisLine = line
                thisLine = thisLine.replace("<FIELDNAME>", bitfield["Name"])
                thisLine = thisLine.replace("<FIELDNUMBER>", str(count))
                thisLine = thisLine.replace("<FIELDCOUNT>", str(fieldCount(bitfield)))
                ret +=  thisLine
                count+=1
    return ret 

def msgName(msg):
    return msg["Name"]

def getMath(x, field, cast):
    ret = x
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    if "Scale" in field:
        ret = "(%s * %s)" % (ret, field["Scale"])
    if "Offset" in field:
        ret = "(%s + %s)" % (ret, field["Offset"])
    return ret

def setMath(x, field, cast):
    ret = x
    if "Offset" in field:
        ret = "(%s - %s)" % (ret, field["Offset"])
    if "Scale" in field:
        ret = "%s / %s" % (ret, field["Scale"])
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    return ret

def Mask(numBits):
    return str(hex(2 ** numBits - 1))

def BitfieldName(field, bits):
    #return str(field["Name"]) +str(bits["Name"])
    return str(bits["Name"])
        
