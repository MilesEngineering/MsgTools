#!/usr/bin/env python3
import sys
import yaml
import json
import os
import io
import string
from time import gmtime, strftime

from MsgUtils import *

class MessageException(Exception):
    pass

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputfile\n')
    sys.exit(1)

def readFile(filename):
    #print("Processing ", filename)
    if filename.endswith(".yaml"):
        inFile = io.open(filename)
        return yaml.load(inFile)
    elif filename.endswith(".json"):
        inFile = io.open(filename)
        return json.load(inFile)
    else:
        return 0

def Messages(inFile):
    return inFile["Messages"]

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
            inFile = readFile(inputFilename)
            if inFile != 0:
                try:
                    ProcessFile(outFile, inFile, subdirComponent)
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

def ProcessMsg(msg, subdirComponent, allowedEnums):
    if "ID" in msg:
        global msgPaths
        global msgNames
        id = msg["ID"]
        if id in msgNames:
            raise MessageException('\nERROR! '+msg['Name']+' uses id '+str(id)+', but already used by '+msgNames[id]+'\n\n')
        if msg['Name'] in msgPaths:
            raise MessageException('\nERROR! '+subdirComponent+'/'+msg['Name']+' being processed, but name already used by '+msgPaths[msg['Name']]+'/'+msg['Name']+'.\n\n')
    msgNames[id] = msg['Name']
    msgPaths[msg['Name']] = subdirComponent
    offset = 0
    for field in msg["Fields"]:
        bitOffset = 0
        if not fieldTypeValid(field):
            raise MessageException('field ' + field["Name"] + ' has invalid type ' + field['Type'])
        if "Enum" in field:
            if not field["Enum"] in allowedEnums:
                raise MessageException('bad enum ' + field["Enum"])
            pass
        if "Bitfields" in field:
            for bits in field["Bitfields"]:
                numBits = bits["NumBits"]
                bitOffset += numBits
            if bitOffset > 8*fieldSize(field):
                raise MessageException('too many bits')
            if "Enum" in bits:
                #global allowedEnums
                #if not bits["Enum"] in allowedEnums:
                #    raise MessageException('bad enum')
                pass
        if offset % fieldSize(field) != 0:
            raise MessageException('field ' + field["Name"] + ' is at offset ' + str(offset) + ' but has size ' + str(fieldSize(field)))
        offset += fieldSize(field) * fieldCount(field)
    
    if offset > 128:
        raise MessageException('message ' + msg["Name"] + ' too big\n')

    return (subdirComponent+'/'+msg['Name']).ljust(32) + str(msg['ID']).rjust(5)+'\n'

def ProcessFile(outFile, inFile, subdirComponent):
    allowedEnums = {}
    try:
        for enum in inFile["Enums"]:
            allowedEnums[enum["Name"]] = enum
    except:
        pass
    for msg in Messages(inFile):
        outFile.write(ProcessMsg(msg, subdirComponent, allowedEnums))

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
