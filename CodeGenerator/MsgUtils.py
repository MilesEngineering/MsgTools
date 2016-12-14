import re
import io
import json
import os.path

class MessageException(Exception):
    pass

# create a class to load YAML files, and any YAML files they include
import yaml
class YamlLoader(yaml.Loader):
    def __init__(self, stream):
        self._dirname = os.path.dirname(stream.name)
        yaml.Loader.__init__(self, stream)

    def include(self, node):
        filename = os.path.join(self._dirname, node.value)
        try:
            inFile = io.open(filename, 'r')
            return yaml.load(inFile, YamlLoader)
        except FileNotFoundError:
            raise MessageException("Error loading " + filename + " for include statement [" + node.value + "]")

YamlLoader.add_constructor('!include', YamlLoader.include)

def readFile(filename):
    #print("Processing ", filename)
    if filename.endswith(".yaml"):
        inFile = io.open(filename)
        return yaml.load(inFile, YamlLoader)
    elif filename.endswith(".json"):
        inFile = io.open(filename)
        return json.load(inFile)
    else:
        return 0

def fieldSize(field):
    fieldSizes = {"uint64":8, "uint32":4, "uint16": 2, "uint8": 1, "int64":8, "int32":4, "int16": 2, "int8": 1, "float64":8, "float32":4}
    return fieldSizes[str.lower(field["Type"])]

def msgSize(msg):
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            offset += fieldSize(field) * fieldCount(field)
    return offset

def fieldIsInt(field):
    isInt  = 0
    if "NumBits" in field:
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
    elif "Type" in field and str.lower(field["Type"]) == 'float64':
        minVal = "DBL_MIN"
    elif "Type" in field and str.lower(field["Type"]) == 'float32':
        minVal = "FLT_MIN"
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
    elif "Type" in field and str.lower(field["Type"]) == 'float64':
        maxVal = "DBL_MAX "
    elif "Type" in field and str.lower(field["Type"]) == 'float32':
        maxVal = "FLT_MAX"
    maxVal = fieldItem(field, "Max", maxVal)
    return maxVal

def fieldStorageMin(storageType):
    dict = \
    {"uint64":0, "uint32":0, "uint16": 0, "uint8": 0,
      "int64": -2**63,  "int32":-2**31,  "int16": -2**15,  "int8": -2**7}
    return dict[storageType]

def fieldStorageMax(storageType):
    dict = \
    {"uint64": 2**64-1, "uint32": 2**32-1, "uint16":  2**16-1, "uint8":  2**8-1,
      "int64": 2**63-1,  "int32": 2**31-1,  "int16":  2**15-1,  "int8": 2**7-1}
    return dict[storageType]

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
    if "Fields" in msg:
        for field in msg["Fields"]:
            count+=1
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    count+=1
    return count

def numberOfSubfields(msg):
    count = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    count+=1
            else:
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

def subfieldReplacements(line,msg):
    line = re.sub('<FOREACHSUBFIELD\(', '', line)
    line = re.sub('\)>$', '', line)
    ret = ""
    count = 0
    for field in msg["Fields"]:
        if "Bitfields" in field:
            for bitfield in field["Bitfields"]:
                thisLine = line
                thisLine = thisLine.replace("<FIELDNAME>", bitfield["Name"])
                thisLine = thisLine.replace("<FIELDNUMBER>", str(count))
                thisLine = thisLine.replace("<FIELDCOUNT>", str(fieldCount(bitfield)))
                ret +=  thisLine
                count+=1
        else:
            thisLine = line
            thisLine = thisLine.replace("<FIELDNAME>", field["Name"])
            thisLine = thisLine.replace("<FIELDNUMBER>", str(count))
            thisLine = thisLine.replace("<FIELDCOUNT>", str(fieldCount(field)))
            ret +=  thisLine
            count+=1
    return ret 

def msgName(msg):
    return msg["Name"]

def msgID(msg, enums):
    ret = "<MSGID>"
    if "IDs" in msg:
        ret = 0
        # iterate over list of keys
        previousShift = 0
        for id in msg["IDs"]:
            value = id["Value"]
            #print("got value " + str(value))
            try:
                value = int(value)
            except ValueError:
                for enum in enums:
                    enumType = enum["Name"]
                    for option in enum["Options"]:
                        if value == enumType + "." + option["Name"]:
                            enumName = value
                            value = int(option["Value"])
                            #print("found value " + str(value) + " for " + enumType + "." + str(enumName))
                            break
            try:
                value = int(value)
            except ValueError:
                raise MessageException("ERROR! Can't find value for " + str(value))
            ret = (ret << previousShift) + value
            #print("ret is now " + str(ret))
            previousShift += id["Bits"]
        ret = hex(ret)
    if "ID" in msg:
        ret = msg["ID"]
    return str(ret)

def Enums(inputData):
    enumList = []
    if "Enums" in inputData:
        enumList = inputData["Enums"]
    if "includes" in inputData:
        for data in inputData["includes"]:
            enumList = enumList + Enums(data)
    return enumList

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
        
