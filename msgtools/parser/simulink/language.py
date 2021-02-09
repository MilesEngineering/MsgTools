import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

def outputSubdir(outDir, filename):
    return outDir + "/+" + filename

def outputFilename(outDir, inputName, templateFilename):
    base = "Input"
    if "output" in templateFilename.lower():
        base = "Output"
    justFilename = base + inputName + '.' + os.path.basename(templateFilename).split('.')[1]
    outputFilename = outDir + "/" + justFilename
    return outputFilename

def accessors(msg):
    return []

def enums(e):
    return ""

def declarations(msg):
    return []

def fieldDefault(field):
    return "0"

def initCode(msg):
    return []

def undefinedMsgId():
    return "-1"

def getMsgID(msg):
    ret = ""
    if "Fields" in msg:
        for field in msg["Fields"]:
            if "IDBits" in field:
                numBits = field["IDBits"]
                if "Enum" in field:
                    pass
                getStr = "obj."+matlabFieldName(msg,field)
                if "Enum" in field:
                    getStr += "AsInt"
                getStr = "uint32("+getStr+")"
                ret =  addShift(ret, getStr, numBits)
            if "Bitfields" in field:
                for bitfield in field["Bitfields"]:
                    if "IDBits" in bitfield:
                        numBits = bitfield["IDBits"]
                        if "Enum" in bitfield:
                            pass
                        getStr = "obj."+BitfieldName(field, bitfield)
                        if "Enum" in bitfield:
                            getStr += "AsInt"
                        getStr = "uint32("+getStr+")"
                        ret =  addShift(ret, getStr, numBits)
    return ret
    
def setMsgID(msg):
    ret = ""
    numBits = 0
    if "Fields" in msg:
        for field in reversed(msg["Fields"]):
            if "IDBits" in field:
                if numBits != 0:
                    ret += "\nid = bitshift(id, -" + str(numBits)+")\n"
                numBits = field["IDBits"]
                setStr = "bitand(id, "+Mask(numBits)+")"
                #if "Enum" in field:
                #    setStr = field["Enum"]+"("+setStr+")"
                ret +=  "obj."+matlabFieldName(msg,field)+" = "+setStr
            if "Bitfields" in field:
                for bitfield in reversed(field["Bitfields"]):
                    if "IDBits" in bitfield:
                        if numBits != 0:
                            ret += "\nid = id >> " + str(numBits)+"\n"
                        numBits = bitfield["IDBits"]
                        setStr = "bitand(id, "+Mask(numBits)+")"
                        #if "Enum" in bitfield:
                        #    setStr = bitfield["Enum"]+"("+setStr+")"
                        ret +=  "obj."+bitfield["Name"]+" = "+setStr
    return ret

oneOutputFilePerMsg = True
