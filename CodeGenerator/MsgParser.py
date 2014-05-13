#!/usr/bin/python3
import sys
import yaml
import json
import os
import io
import string
from time import gmtime, strftime

from MsgUtils import *

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputdir language template\n')
    sys.exit(1)

def readFile(filename):
    #print("Processing ", filename)
    if filename.find(".yaml") != -1:
        inFile = io.open(filename)
        return yaml.load(inFile)
    elif filename.find(".json") != -1:
        inFile = io.open(filename)
        return json.load(inFile)
    else:
        return NULL

def Messages(inFile):
    return inFile["Messages"]

def Enums(inFile):
    try:
        return inFile["Enums"]
    except:
        return {}

def replace(line, pattern, replacement):
    if pattern in line:
        ret = ""
        #print("replacing ", pattern, " with ", replacement)
        for newLine in replacement.split('\n'):
            ret += line.replace(pattern, newLine)
    else:
        #print("NOT replacing ", pattern, " with ", replacement, " in ", line)
        ret = line
    return ret

def DoReplacements(line, msg, enums):
    ret = line + '\n'
    ret = replace(ret, "<MSGNAME>", msgName(msg))
    if "ID" in msg:
        ret = replace(ret, "<MSGID>", str(msg["ID"]))
    ret = replace(ret, "<MSGSIZE>", str(language.msgSize(msg)))
    ret = replace(ret, "<ENUMERATIONS>", language.enums(enums))
    ret = replace(ret, "<ACCESSORS>", "\n".join(language.accessors(msg)))
    ret = replace(ret, "<INIT_CODE>", "\n".join(language.initCode(msg)))
    ret = replace(ret, "<OUTPUTFILENAME>", outputFilename)
    ret = replace(ret, "<INPUTFILENAME>", inputFilename)
    ret = replace(ret, "<TEMPLATEFILENAME>", templateFilename)
    ret = replace(ret, "<LANGUAGEFILENAME>", languageFilename)
    ret = replace(ret, "<DATE>", currentDateTime)
    return ret

def ProcessFile(template, inFile, outFile):
    for msg in Messages(inFile):
        for line in template:
            line = DoReplacements(line, msg, Enums(inFile))
            outFile.write(line)

def Mask(numBits):
    return str(hex(2 ** numBits - 1))
        
# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        Usage();
    msgDir = sys.argv[1]
    outDir = sys.argv[2]
    languageFilename = sys.argv[3]
    templateFilename = sys.argv[4]
    
    currentDateTime = strftime("%d/%m/%Y at %H:%M:%S")
    
    # import the language file
    sys.path.append(os.path.dirname(languageFilename))
    language = languageFilename
    import language

    # read the template file
    with open(templateFilename, 'r') as templateFile:
        template = templateFile.read().splitlines() 
    
    # loop over input message files
    for filename in os.listdir(msgDir):
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            continue
        inFile = readFile(inputFilename);
        outputFilename = outDir + "/" + filename.split('.')[0] + '.' + os.path.basename(templateFilename).split('.')[1]
        print("Creating", outputFilename)
        # \todo! How to write a try with no except: statements?
        try:
            os.makedirs(os.path.dirname(outputFilename))
        except:
            a=1
        with open(outputFilename,'w') as outFile:
            ProcessFile(template, inFile, outFile)
