#!/usr/bin/env python3
import sys
import os
import string
from time import gmtime, strftime

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.parser.MsgUtils import *

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputfile\n')
    sys.exit(1)

def Messages(inputData):
    return inputData["Messages"]

def ProcessDir(outFile, msgDir, subdirComponent, isHeaderDir):
    for filename in sorted(os.listdir(msgDir)):
        global inputFilename
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            subdirParam = filename
            if subdirComponent != "":
                subdirParam = subdirComponent + "/" + subdirParam
            ProcessDir(outFile, inputFilename, subdirParam, filename=='headers' or isHeaderDir)
        else:
            try:
                inputData = readFile(inputFilename)
                if inputData != 0:
                    ProcessFile(filename, outFile, inputData, subdirComponent, isHeaderDir)
            except MessageException as e:
                sys.stderr.write('Error in ' + inputFilename)
                sys.stderr.write('\n'+str(e)+'\n')
                outFile.close()
                os.remove(outFile.name)
                sys.exit(1)
            except:
                sys.stderr.write("\nError in " + inputFilename + "!\n\n")
                outFile.close()
                os.remove(outFile.name)
                raise

def fieldTypeValid(field):
    allowedFieldTypes = \
    ["uint64", "uint32", "uint16", "uint8",
      "int64",  "int32",  "int16",  "int8",
      "float64", "float32"]
    return field["Type"] in allowedFieldTypes

def ProcessMsg(filename, msg, subdirComponent, enums, isHeader):
    enumNames = {}
    for enum in enums:
        enumNames[enum["Name"]] = enum
    
    if not isHeader:
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
    if "Fields" in msg:
        fieldNames = {}
        for field in msg["Fields"]:
            bitOffset = 0
            if not re.match("^[\w\d_]+$", field["Name"]):
                raise MessageException('bad field name [' + field["Name"]+"] in message "+msgName(msg))
            if field["Name"] in fieldNames:
                raise MessageException('Duplicate field name [' + field["Name"]+"] in message "+msgName(msg))
            fieldNames[field["Name"]] = field["Name"]
            if not fieldTypeValid(field):
                raise MessageException('field ' + field["Name"] + ' has invalid type ' + field["Type"]+ " in message "+msgName(msg))
            if "Enum" in field:
                if not field["Enum"] in enumNames:
                    raise MessageException('bad enum [' + field["Enum"]+"] in message "+msgName(msg))
                if " " in field["Enum"]:
                    raise MessageException('bad enum [' + field["Enum"]+"] in message "+msgName(msg))
                pass
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    bitOffset += numBits
                    if not re.match("^[\w\d_]+$", bits["Name"]):
                        raise MessageException('bad bitfield name [' + bits["Name"]+"] in message "+msgName(msg))
                    if bits["Name"] in fieldNames:
                        raise MessageException('Duplicate bitfield name [' + bits["Name"]+"] in field ["+field["Name"]+"] in message "+msgName(msg))
                    fieldNames[bits["Name"]] = bits["Name"]
                if bitOffset > 8*fieldSize(field):
                    raise MessageException('too many bits in message '+msgName(msg))
                if "Enum" in bits:
                    if not bits["Enum"] in enumNames:
                        raise MessageException('bad enum in message '+msgName(msg))
                    pass
    if isHeader:
        return ''
    return (subdirComponent+'/'+msgName(msg)).ljust(35) +" "+(subdirComponent+'/'+filename).ljust(40) +" "+ str(id).rjust(10)+'\n'

def ProcessFile(filename, outFile, inputData, subdirComponent, isHeader):
    enums = Enums(inputData)
    ids = MsgIDs(inputData)
    
    PatchStructs(inputData)

    if "Messages" in inputData:
        for msg in Messages(inputData):
            msg["ids"] = ids
            outFile.write(ProcessMsg(filename, msg, subdirComponent, enums, isHeader))

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
        ProcessDir(outFile, msgDir, "", msgDir.endswith('/headers'))
        if len(sys.argv) > 3:
            msgDir = sys.argv[3]
            ProcessDir(outFile, msgDir, "", msgDir.endswith('/headers'))

# main starts here
if __name__ == '__main__':
    main()
