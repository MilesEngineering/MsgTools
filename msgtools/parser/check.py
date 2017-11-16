#!/usr/bin/env python3
import sys
import os
import string
from time import gmtime, strftime

try:
    from msgtools.parser.MsgUtils import *
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.parser.MsgUtils import *

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputfile\n')
    sys.exit(1)

def Messages(inputData):
    return inputData["Messages"]

def ProcessDir(outFile, msgDir, subdirComponent):
    for filename in sorted(os.listdir(msgDir)):
        global inputFilename
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            if filename != 'headers':
                subdirParam = filename
                if subdirComponent != "":
                    subdirParam = subdirComponent + "/" + subdirParam
                ProcessDir(outFile, inputFilename, subdirParam)
        else:
            try:
                inputData = readFile(inputFilename)
                if inputData != 0:
                    ProcessFile(filename, outFile, inputData, subdirComponent)
            except MessageException as e:
                sys.stderr.write('Error in ' + inputFilename)
                sys.stderr.write('\n'+str(e)+'\n')
                outFile.close()
                os.remove(outputFilename)
                sys.exit(1)
            except:
                sys.stderr.write("\nError in " + inputFilename + "!\n\n")
                outFile.close()
                os.remove(outputFilename)
                raise

def fieldTypeValid(field):
    allowedFieldTypes = \
    ["uint64", "uint32", "uint16", "uint8",
      "int64",  "int32",  "int16",  "int8",
      "float64", "float32"]
    return field["Type"] in allowedFieldTypes

def ProcessMsg(filename, msg, subdirComponent, enums):
    enumNames = {}
    for enum in enums:
        enumNames[enum["Name"]] = enum
    
    id = msgID(msg, enums, -1)
    idInt = int(id, 0)
    if idInt:
        global msgNames
        fullMsgName = subdirComponent+'/'+msgName(msg)
        if idInt in msgNames:
            raise MessageException('\nERROR! '+fullMsgName+' uses id '+str(id)+', but already used by '+msgNames[idInt]+'\n\n')
        if fullMsgName in msgNames:
            raise MessageException('\nERROR! '+fullMsgName+' being processed, but name already used by '+msg['Name']+'.\n\n')
        msgNames[idInt] = fullMsgName
    offset = 0
    if "Fields" in msg:
        fieldNames = {}
        for field in msg["Fields"]:
            bitOffset = 0
            if not re.match("^[\w\d_]+$", field["Name"]):
                raise MessageException('bad field name [' + field["Name"]+"]")
            if field["Name"] in fieldNames:
                raise MessageException('Duplicate field name [' + field["Name"]+"]")
            fieldNames[field["Name"]] = field["Name"]
            if not fieldTypeValid(field):
                raise MessageException('field ' + field["Name"] + ' has invalid type ' + field['Type'])
            if "Enum" in field:
                if not field["Enum"] in enumNames:
                    raise MessageException('bad enum [' + field["Enum"]+"]")
                if " " in field["Enum"]:
                    raise MessageException('bad enum [' + field["Enum"]+"]")
                pass
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    bitOffset += numBits
                    if not re.match("^[\w\d_]+$", bits["Name"]):
                        raise MessageException('bad bitfield name [' + bits["Name"]+"]")
                    if bits["Name"] in fieldNames:
                        raise MessageException('Duplicate bitfield name [' + bits["Name"]+"] in field ["+field["Name"]+"]")
                    fieldNames[bits["Name"]] = bits["Name"]
                if bitOffset > 8*fieldSize(field):
                    raise MessageException('too many bits')
                if "Enum" in bits:
                    if not bits["Enum"] in enumNames:
                        raise MessageException('bad enum')
                    pass
            # disable enforcement of native alignment
            #if offset % fieldSize(field) != 0:
            #    raise MessageException('field ' + field["Name"] + ' is at offset ' + str(offset) + ' but has size ' + str(fieldSize(field)))
            offset += fieldSize(field) * fieldCount(field)
    
    return (subdirComponent+'/'+msgName(msg)).ljust(35) +" "+(subdirComponent+'/'+filename).ljust(40) +" "+ str(id).rjust(10)+'\n'

def ProcessFile(filename, outFile, inputData, subdirComponent):
    enums = Enums(inputData)
    ids = MsgIDs(inputData)

    if "Messages" in inputData:
        for msg in Messages(inputData):
            msg["ids"] = ids
            outFile.write(ProcessMsg(filename, msg, subdirComponent, enums))

def main(args=None):
    if len(sys.argv) < 3:
        Usage();
    outputFilename = sys.argv[1]
    msgDir = sys.argv[2]
    
    global msgNames
    msgNames = {}

    try:
        os.makedirs(os.path.dirname(outputFilename))
    except:
        pass
    with open(outputFilename,'w') as outFile:
        # loop over input message files
        ProcessDir(outFile, msgDir, "")
        if len(sys.argv) > 3:
            msgDir = sys.argv[3]
            ProcessDir(outFile, msgDir, "")

# main starts here
if __name__ == '__main__':
    main()
