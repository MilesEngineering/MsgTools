#!/usr/bin/env python3
import sys
import os
import string
from time import gmtime, strftime

from MsgUtils import *

class MessageException(Exception):
    pass

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
            inputData = readFile(inputFilename)
            if inputData != 0:
                try:
                    ProcessFile(outFile, inputData, subdirComponent)
                except MessageException as e:
                    sys.stderr.write('Error in ' + inputFilename)
                    sys.stderr.write('\n'+str(e)+'\n')
                    outFile.close()
                    os.remove(outputFilename)
                    sys.exit(1)

def fieldTypeValid(field):
    allowedFieldTypes = \
    ["uint64", "uint32", "uint16", "uint8",
      "int64",  "int32",  "int16",  "int8",
      "float64", "float32"]
    return field["Type"] in allowedFieldTypes

def ProcessMsg(msg, subdirComponent, enums):
    enumNames = {}
    for enum in enums:
        enumNames[enum["Name"]] = enum

    id = msgID(msg, enums)
    idInt = int(id, 0)
    if "ID" in msg or "IDs" in msg:
        global msgPaths
        global msgNames
        if idInt in msgNames:
            raise MessageException('\nERROR! '+msg['Name']+' uses id '+str(id)+', but already used by '+msgNames[idInt]+'\n\n')
        if msg['Name'] in msgPaths:
            raise MessageException('\nERROR! '+subdirComponent+'/'+msg['Name']+' being processed, but name already used by '+msgPaths[msg['Name']]+'/'+msg['Name']+'.\n\n')
    msgNames[idInt] = msg['Name']
    msgPaths[msg['Name']] = subdirComponent
    offset = 0
    for field in msg["Fields"]:
        bitOffset = 0
        if not fieldTypeValid(field):
            raise MessageException('field ' + field["Name"] + ' has invalid type ' + field['Type'])
        if "Enum" in field:
            if not field["Enum"] in enumNames:
                raise MessageException('bad enum ' + field["Enum"])
            pass
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                bitOffset += numBits
            if bitOffset > 8*fieldSize(field):
                raise MessageException('too many bits')
            if "Enum" in bits:
                if not bits["Enum"] in enumNames:
                    raise MessageException('bad enum')
                pass
        if offset % fieldSize(field) != 0:
            raise MessageException('field ' + field["Name"] + ' is at offset ' + str(offset) + ' but has size ' + str(fieldSize(field)))
        offset += fieldSize(field) * fieldCount(field)
    
    if offset > 128:
        raise MessageException('message ' + msg["Name"] + ' too big\n')

    return (subdirComponent+'/'+msg['Name']).ljust(32) + str(id).rjust(5)+'\n'

def ProcessFile(outFile, inputData, subdirComponent):
    enums = Enums(inputData)

    if "Messages" in inputData:
        for msg in Messages(inputData):
            outFile.write(ProcessMsg(msg, subdirComponent, enums))

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 3:
        Usage();
    outputFilename = sys.argv[1]
    msgDir = sys.argv[2]
    
    global msgNames
    msgNames = {}
    global msgPaths
    msgPaths = {}

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
