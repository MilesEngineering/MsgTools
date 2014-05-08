#!/usr/bin/python3
import sys
import yaml
import json
import os
import io
import string
from time import gmtime, strftime

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputdir language template\n')
    sys.exit(1)

def readFile(filename):
    print("Processing ", filename)
    if filename.find(".yaml") != -1:
        inFile = io.open(filename)
        return yaml.load(inFile)
    elif filename.find(".json") != -1:
        inFile = io.open(filename)
        return json.load(inFile)
    else:
        return NULL

def printMessage(msg, outFile):
    #print msg["Name"] + ": " + msg["Description"]
    #for field in msg["Fields"]:
    #    print field["Name"] + ": " + field["Type"]
    outFile.write("\n".join(language.accessors(msg)))

def fieldSize(field):
    fieldSizes = {"uint64":8, "uint32":4, "uint16": 2, "uint8": 1, "int64":8, "int32":4, "int16": 2, "int8": 1, "float64":8, "float32":4}
    return fieldSizes[str.lower(field["Type"])]

def fieldUnits(field):
    if "Units" in field:
        return field["Units"]
    else:
        return ""

def fieldDescription(field):
    if "Description" in field:
        return field["Description"]
    else:
        return ""

def fieldDefault(field):
    if "Default" in field:
        return field["Default"]
    else:
        return ""

def fieldCount(field):
    if "Count" in field and field["Count"] > 1:
        return field["Count"]
    else:
        return 1

def msgName(msg):
    return msg["Name"]

def Messages(inFile):
    return inFile["Messages"]

def Enums(inFile):
    return inFile["Enums"]

def printEnums(inFile):
    if "Enums" in inFile:
        for enum in Enums(inFile):
            outFile.write("Enum " + enum["Name"] + ":\n")
            for option in enum["Options"]:
                outFile.write("    " + option["Name"] + " = " + str(option["Value"]) + "\n")
        outFile.write("\n");

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

def DoReplacements(line, msg):
    ret = line + '\n'
    ret = replace(ret, "<MSGNAME>", msgName(msg))
    if "ID" in msg:
        ret = replace(ret, "<MSGID>", msg["ID"])
    ret = replace(ret, "<MSGSIZE>", str(language.msgSize(msg)))
    #ret = replace(ret, "<ENUMERATIONS>", language.enums(msg))
    ret = replace(ret, "<ACCESSORS>", "\n".join(language.accessors(msg)))
    ret = replace(ret, "<INIT_CODE>", "\n".join(language.initCode(msg)))
    ret = replace(ret, "<OUTPUTFILENAME>", outputFilename)
    ret = replace(ret, "<INPUTFILENAME>", inputFilename)
    ret = replace(ret, "<TEMPLATEFILENAME>", templateFilename)
    ret = replace(ret, "<LANGUAGEFILENAME>", languageFilename)
    ret = replace(ret, "<DATE>", currentDateTime)
    return ret

def ProcessFile(template, inFile, outFile):
    #printEnums(inFile)
    for msg in Messages(inFile):
        printMessage(msg, outFile)
        for line in template:
            line = DoReplacements(line, msg)
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
        inFile = readFile(inputFilename);
        outputFilename = outDir + "/" + filename.split('.')[0] + '.' + os.path.basename(templateFilename).split('.')[1]
        print("Creating ", outputFilename)
        # \todo! How to write a try with no except: statements?
        try:
            os.makedirs(os.path.dirname(outputFilename))
        except:
            print("")
        with open(outputFilename,'w') as outFile:
            ProcessFile(template, inFile, outFile)
    print("")
