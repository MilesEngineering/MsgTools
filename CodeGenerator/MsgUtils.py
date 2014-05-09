def fieldSize(field):
    fieldSizes = {"uint64":8, "uint32":4, "uint16": 2, "uint8": 1, "int64":8, "int32":4, "int16": 2, "int8": 1, "float64":8, "float32":4}
    return fieldSizes[str.lower(field["Type"])]

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

def msgName(msg):
    return msg["Name"]

def getMath(x, field, cast):
    ret = x
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    if "Scale" in field:
        ret = "(%s / %s)" % (ret, field["Scale"])
    if "Offset" in field:
        ret = "(%s + %s)" % (ret, field["Offset"])
    return ret

def setMath(x, field, cast):
    ret = x
    if "Offset" in field:
        ret = "(%s - %s)" % (ret, field["Offset"])
    if "Scale" in field:
        ret = "%s * %s" % (ret, field["Scale"])
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    return ret
