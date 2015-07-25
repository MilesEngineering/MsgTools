#!/usr/bin/env python3
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
        return 0

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

def DoReplacements(line, msg, enums, subdirComponent):
    ret = line + '\n'
    ret = replace(ret, "<MSGNAME>", msgName(msg))
    if "ID" in msg:
        ret = replace(ret, "<MSGID>", str(msg["ID"]))
    ret = replace(ret, "<MSGSIZE>", str(language.msgSize(msg)))
    ret = replace(ret, "<MSGDESCRIPTION>", str(msg["Description"]))
    ret = replace(ret, "<ENUMERATIONS>", language.enums(enums))
    ret = replace(ret, "<ACCESSORS>", "\n".join(language.accessors(msg)))
    ret = replace(ret, "<REFLECTION>", language.reflection(msg))
    ret = replace(ret, "<INIT_CODE>", "\n".join(language.initCode(msg)))
    ret = replace(ret, "<OUTPUTFILENAME>", outputFilename)
    ret = replace(ret, "<INPUTFILENAME>", inputFilename)
    ret = replace(ret, "<TEMPLATEFILENAME>", templateFilename)
    ret = replace(ret, "<LANGUAGEFILENAME>", languageFilename)
    ret = replace(ret, "<MESSAGE_SUBDIR>", subdirComponent)
    ret = replace(ret, "<DATE>", currentDateTime)
    return ret

def ProcessDir(template, msgDir, subdirComponent):
    for filename in os.listdir(msgDir):
        global inputFilename
        inputFilename = msgDir + '/' + filename
        global outputFilename
        outputFilename = outDir
        if subdirComponent != "":
            outputFilename += "/" + subdirComponent
        outputFilename += "/" + filename.split('.')[0] + '.' + os.path.basename(templateFilename).split('.')[1]
        if os.path.isdir(inputFilename):
            if filename != 'headers':
                ProcessDir(template, msgDir + '/' + inputFilename, filename)
        else:
            inputFileTime = os.path.getmtime(inputFilename)
            try:
                outputFileTime = os.path.getmtime(outputFilename)
            except:
                outputFileTime = 0
            if (inputFileTime > outputFileTime or templateFileTime > outputFileTime or languageFileTime > outputFileTime):
                inFile = readFile(inputFilename)
                if inFile != 0:
                    print("Creating", outputFilename)
                    try:
                        os.makedirs(os.path.dirname(outputFilename))
                    except:
                        pass
                    with open(outputFilename,'w') as outFile:
                        ProcessFile(template, inFile, outFile, subdirComponent)
    

def ProcessFile(template, inFile, outFile, subdirComponent):
    for msg in Messages(inFile):
        for line in template:
            line = DoReplacements(line, msg, Enums(inFile), subdirComponent)
            outFile.write(line)

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

    templateFileTime = os.path.getmtime(templateFilename)
    languageFileTime = os.path.getmtime(languageFilename)
    
    # read the template file
    with open(templateFilename, 'r') as templateFile:
        template = templateFile.read().splitlines() 
    
    # loop over input message files
    ProcessDir(template, msgDir, "")
