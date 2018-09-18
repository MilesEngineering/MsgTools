import re
import io
import json
import os.path
import copy

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

    def loadFile(self, node):
        filename = os.path.join(self._dirname, node.value)
        return "*Not* including " + filename

YamlLoader.add_constructor('!include', YamlLoader.include)
YamlLoader.add_constructor('!File', YamlLoader.loadFile)

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
        maxVal = "DBL_MAX"
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
    ret = fieldItem(field, "Description", "")
    if not ret:
        ret = ""
    ret = ret.replace('\n', ' ')
    ret = ret.replace('\\', ' ')
    return ret

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
    try:
        return msg["Name"]
    except KeyError:
        pass
    ret = None
    # iterate over list of ids
    for id in msg["ids"]:
        subname = msg[id["Name"]]
        if "." in subname:
            subname = subname.split(".")[1]
        if ret:
            ret = ret + "_" + subname
        else:
            ret = subname
    return ret

def msgAlias(msg):
    try:
        return msg["Alias"]
    except KeyError:
        return ""
    
def msgShortName(msg):
    commonSubdir = msg["commonSubdir"]
    name = msgName(msg)
    # remove subdirs from start
    if name.startswith(commonSubdir+"_"):
        name = name.replace(commonSubdir+"_", "")
    return name

def msgID(msg, enums, undefinedMsgId):
    ret = undefinedMsgId
    # check if there was an externally specified list of ID fields
    if msg["ids"]:
        try:
            ret = 0
            # iterate over list of ids
            shiftValue = 0
            for id in msg["ids"]:
                value = msg[id["Name"]]
                #print("got value " + str(value))
                try:
                    value = int(value)
                except ValueError:
                    for enum in enums:
                        enumType = enum["Name"]
                        for option in enum["Options"]:
                            if value == enumType + "." + option["Name"] or (enum["Name"] == id["Name"]+"s" and value == option["Name"]):
                                enumName = value
                                value = int(option["Value"])
                                #print("found value " + str(value) + " for " + enumType + "." + str(enumName))
                                break
                try:
                    value = int(value)
                except ValueError:
                    raise MessageException("ERROR! Can't find value for " + str(value))
                shiftValue = id["Bits"]
                #print("ID " + id["Name"] + " is " + str(value) + ", " + str(id["Bits"]) + " bits")
                ret = (ret << shiftValue) + value
        except KeyError:
            pass
    if "ID" in msg:
        ret = msg["ID"]
    #print("message " + msg["Name"] + " has ID " + hex(ret))
    return str(ret)

def msgDescriptor(msg, inputFilename):
    subdir = msg["commonSubdir"]
    name = msgName(msg)
    basename = os.path.basename(inputFilename).split('.')[0]
    # add the filename as a namespace, unless it's already there
    if not basename == name and not basename+'_' in name:
        name = basename + '.' + name
        print("adding basename " + basename + " to " + name)
    if name.startswith(subdir+"_"):
        return name.replace("_", ".")
    if subdir and not name.startswith(subdir):
        return subdir+"."+name.replace("_", ".")
    return name

def addShift(base, value, shiftValue):
    ret = value
    if base != "":
        ret = "(("+base+")<<"+str(shiftValue)+")"+"+"+value
    return ret
    
def baseGetMsgID(prefix, baseParam, typecast, enumAsIntParam, msg):
    ret = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = field["IDBits"]
                param = baseParam
                if "Enum" in field and enumAsIntParam:
                    if param != "":
                        param += ", "
                    param += "1"
                getStr = prefix+"Get"+field["Name"]+"("+param+")"
                if typecast == "CAST_ALL" or ("Enum" in field and typecast != 0):
                    getStr = "(uint32_t)("+getStr+")"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        param = baseParam
                        if "Enum" in bitfield and enumAsIntParam:
                            if param != "":
                                param += ", "
                            param += "1"
                        getStr = prefix+"Get"+BitfieldName(field, bitfield)+"("+param+")"
                        if typecast == "CAST_ALL" or ("Enum" in bitfield and typecast != 0):
                            getStr = "(uint32_t)("+getStr+")"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def baseSetMsgID(prefix, param, castEnums, enumAsIntParam, msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nid = id >> " + str(numBits)+"\n"
                numBits = field["IDBits"]
                setStr = "id & "+Mask(numBits)
                if "Enum" in field and castEnums:
                    setStr = field["Enum"]+"("+setStr+")"
                ret +=  prefix+"Set"+field["Name"]+"("+param+setStr+")"
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = id >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "id & "+Mask(numBits)
                        if "Enum" in bitfield and castEnums:
                            setStr = bitfield["Enum"]+"("+setStr+")"
                        ret +=  prefix+"Set"+bitfield["Name"]+"("+param+setStr+")"
    return ret

# return a list of all enumerations in this input file, or anything it includes
def Enums(inputData):
    enumList = []
    if "Enums" in inputData:
        enumList = inputData["Enums"]
    if "includes" in inputData:
        for data in inputData["includes"]:
            enumList = enumList + Enums(data)
    return enumList

def Structs(inputData):
    structList = []
    if "Structs" in inputData:
        structList = inputData["Structs"]
    if "includes" in inputData:
        for data in inputData["includes"]:
            structList = structList + Structs(data)
    return structList

# this replaces fields that are references to structs with the fields from the referenced struct
def PatchStructs(inputData):
    # loop twice, so that references to structs inside structs are also replaced
    for i in range(2):
        structs = Structs(inputData)
        if not structs:
            return
        
        # need to make a new list, because we'll be inserting elements as we iterate
        if 'Messages' in inputData:
            for msg in inputData["Messages"]:
                if 'Fields' in msg:
                    outfields = []
                    for field in msg['Fields']:
                        if field['Type'] in structs:
                            s = structs[field['Type']]
                            for subfield in s['Fields']:
                                subfieldcopy = copy.deepcopy(subfield)
                                subfieldcopy['Name'] = field['Name'] + "_" + subfield['Name']
                                if "Bitfields" in subfieldcopy:
                                    for bits in subfieldcopy["Bitfields"]:
                                        bits['Name'] = field['Name'] + "_" + bits['Name']
                                outfields.append(subfieldcopy)
                        else:
                            outfields.append(field)
                    msg['Fields'] = outfields

# sanitize the option name, to have valid identifier characters
def OptionName(option):
    return option["Name"].replace("/", "_or_").replace(" ", "_").replace("-", "_")

# return a list of all IDs in this input file, or anything it includes
def MsgIDs(inputData):
    idList = []
    if "IDs" in inputData:
        idList = inputData["IDs"]
    if "includes" in inputData:
        for data in inputData["includes"]:
            idList = idList + MsgIDs(data)
    return idList

# return a list of just the enums that are used by a message's fields/bitfields
# this is useful for languages that put enum info into their output file, because
# it will be a list of only the enums that are relevant.  often there can be many
# enums defiined in a common include file, and they aren't all used by a particular
# message
def UsedEnums(msg, enums):
    usedEnums = []
    for enum in enums:
        if "Fields" in msg:
            for field in msg["Fields"]:
                if "Enum" in field:
                    if field["Enum"] == enum["Name"]:
                        usedEnums.append(enum)
                        break
                foundEnum = 0
                if "Bitfields" in field:
                    for bits in field["Bitfields"]:
                        if "Enum" in bits:
                            if bits["Enum"] == enum["Name"]:
                                usedEnums.append(enum)
                                foundEnum = 1
                                break
                    if foundEnum:
                        break

    try:
        if msg["ids"]:
            idEnum = {}
            idEnum["Name"] = "IDs"
            idEnum["Options"] = []
            for id in msg["ids"]:
                idName = id["Name"]
                idValue = msg[idName]
                try:
                    idValue = int(idValue)
                except ValueError:
                    for enum in enums:
                        enumType = enum["Name"]
                        for option in enum["Options"]:
                            if idValue == enumType + "." + option["Name"] or (enum["Name"] == id["Name"]+"s" and idValue == option["Name"]):
                                enumName = idValue
                                idValue = int(option["Value"])
                                break
                try:
                    idValue = int(idValue)
                except ValueError:
                    raise MessageException("ERROR! Can't find value for " + str(idValue))
                option = {}
                option["Name"] = idName
                option["Value"] = idValue
                idEnum["Options"].append(option)
            usedEnums.append(idEnum)
    except KeyError:
        pass
    return usedEnums

def typeForScaledInt(field):
    numBits = fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "float"

# for floats, append tag such as 'f' to constants to eliminate compiler warnings
def fieldScale(field, floatTag):
    if "Scale" in field:
        ret = field["Scale"]
        if typeForScaledInt(field) == "float":
            ret = str(ret) + floatTag
    return ret

def fieldOffset(field, floatTag):
    if "Offset" in field:
        ret = field["Offset"]
        if typeForScaledInt(field) == "float":
            ret = str(ret) + floatTag
    return ret

# add tag (such as 'f') to scale and offset for floats
def getMath(x, field, cast, floatTag=""):
    ret = x
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    if "Scale" in field:
        ret = "(%s * %s)" % (ret, fieldScale(field, floatTag))
    if "Offset" in field:
        ret = "(%s + %s)" % (ret, fieldOffset(field, floatTag))
    return ret

def setMath(x, field, cast, floatTag=""):
    ret = x
    if "Offset" in field:
        ret = "(%s - %s)" % (ret, fieldOffset(field, floatTag))
    if "Scale" in field:
        ret = "%s / %s" % (ret, fieldScale(field, floatTag))
    if cast and ("Offset" in field or "Scale" in field):
        ret = "%s(%s)" % (cast, ret)
    return ret

def Mask(numBits):
    return str(hex(2 ** numBits - 1))

def BitfieldName(field, bits):
    #return str(field["Name"]) +str(bits["Name"])
    return str(bits["Name"])
        
