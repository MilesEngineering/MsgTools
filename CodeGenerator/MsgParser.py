#!/usr/bin/env python3
import sys
import yaml
import json
import os
import io
import string
from time import gmtime, strftime

from MsgUtils import *

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

def optionalReplace(line, pattern, fn, param):
    if pattern in line:
        method = getattr(language, fn)
        return replace(line, pattern, method(param))
    return line

def DoReplacements(line, msg, enums, subdirComponent):
    ret = line + '\n'
    ret = replace(ret, "<MSGNAME>", msgName(msg))
    ret = replace(ret, "<NUMBER_OF_FIELDS>", str(numberOfFields(msg)))
    ret = replace(ret, "<NUMBER_OF_SUBFIELDS>", str(numberOfSubfields(msg)))
    if "ID" in msg:
        ret = replace(ret, "<MSGID>", str(msg["ID"]))
    ret = replace(ret, "<MSGSIZE>", str(language.msgSize(msg)))
    ret = replace(ret, "<MSGDESCRIPTION>", str(msg["Description"]))
    ret = optionalReplace(ret, "<ENUMERATIONS>", 'enums', enums)
    ret = replace(ret, "<ACCESSORS>", "\n".join(language.accessors(msg)))
    ret = optionalReplace(ret, "<REFLECTION>", 'reflection', msg)
    ret = optionalReplace(ret, "<FIELDINFOS>", 'fieldInfos', msg)
    ret = optionalReplace(ret, "<STRUCTUNPACKING>", 'structUnpacking', msg)
    ret = optionalReplace(ret, "<STRUCTPACKING>", 'structPacking', msg)
    ret = replace(ret, "<DECLARATIONS>", "\n".join(language.declarations(msg)))
    ret = replace(ret, "<INIT_CODE>", "\n".join(language.initCode(msg)))
    ret = replace(ret, "<OUTPUTFILENAME>", outputFilename)
    ret = replace(ret, "<INPUTFILENAME>", inputFilename)
    ret = replace(ret, "<TEMPLATEFILENAME>", templateFilename)
    ret = replace(ret, "<LANGUAGEFILENAME>", languageFilename)
    ret = replace(ret, "<MESSAGE_SUBDIR>", subdirComponent)
    ret = replace(ret, "<DATE>", currentDateTime)
    if "<FOREACHFIELD" in ret:
        ret = fieldReplacements(ret, msg)
    if "<FOREACHSUBFIELD" in ret:
        ret = subfieldReplacements(ret, msg)
    
    # ugly, but do this twice, before and after other replacements, because the code generator
    # might insert it while doing other replacements.
    ret = replace(ret, "<MSGNAME>", msgName(msg))
    return ret

def CommonSubdir(f1, f2):
    # find largest string shared at end of 2 filenames
    d1 = os.path.dirname(f1)
    d2 = os.path.dirname(f2)
    minLen = min(len(d1), len(d2))
    subdirComponent = ''
    for i in range(1, minLen):
        if d1[-i] == d2[-i]:
            subdirComponent = d1[-i] + subdirComponent
        else:
            break

    # strip slashes at ends
    return subdirComponent.strip("/")

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        sys.stderr.write('Usage: ' + sys.argv[0] + ' input output language template\n')
        sys.exit(1)
    inputFilename = sys.argv[1]
    outputFilename = sys.argv[2]
    languageFilename = sys.argv[3]
    templateFilename = sys.argv[4]
    commonSubdir = CommonSubdir(inputFilename, outputFilename)
    
    currentDateTime = strftime("%d/%m/%Y at %H:%M:%S")
    
    # import the language file
    sys.path.append(os.path.dirname(languageFilename))
    language = languageFilename
    import language

    # read the template file
    with open(templateFilename, 'r') as templateFile:
        template = templateFile.read().splitlines() 
    
    # read the input file
    inFile = readFile(inputFilename)
    try:
        os.makedirs(os.path.dirname(outputFilename))
    except:
        pass
    with open(outputFilename,'w') as outFile:
        try:
            for msg in Messages(inFile):
                for line in template:
                    line = DoReplacements(line, msg, Enums(inFile), commonSubdir)
                    outFile.write(line)
        except MessageException as e:
            sys.stderr.write(str(e)+'\n')
            outFile.close()
            os.remove(outputFilename)
            sys.exit(1)
