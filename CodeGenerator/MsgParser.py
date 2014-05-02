#!/usr/bin/python
import sys
import yaml
import json
import os
import io
import string

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputdir language template\n')
    sys.exit(1)

def readFile(filename):
    print "Processing " +  filename
    if filename.find(".yaml") != -1:
        file = io.open(filename)
        return yaml.load(file)
    elif filename.find(".json") != -1:
        file = io.open(filename)
        return json.load(file)
    else:
        return NULL

def printMessage(msg, outFile):
    #print msg["Name"] + ": " + msg["Description"]
    #for field in msg["Fields"]:
    #    print field["Name"] + ": " + field["Type"]
    outFile.write(language.accessors(msg))

def fieldSize(field):
    fieldSizes = {"uint64":8, "uint32":4, "uint16": 2, "uint8": 1, "int64":8, "int32":4, "int16": 2, "int8": 1, "float64":8, "float32":4}
    return fieldSizes[str.lower(field["Type"])]

def fieldCount(field):
    if "Count" in field and field["Count"] > 1:
        return field["Count"]
    else:
        return 1

def msgName(msg):
    return msg["Name"]

def Messages(file):
    return file["Messages"]

def Enums(file):
    return file["Enums"]

def ProcessFile(file, outFile):
    if "Enums" in file:
        for enum in Enums(file):
            outFile.write("Enum " + enum["Name"] + ":\n")
            for option in enum["Options"]:
                outFile.write("    " + option["Name"] + " = " + str(option["Value"]) + "\n")
        outFile.write("\n");
    for msg in Messages(file):
        printMessage(msg, outFile)

def Mask(numBits):
    return str(hex(2 ** numBits - 1))
        
# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        Usage();
    msgDir = sys.argv[1]
    outDir = sys.argv[2]
    language = sys.argv[3]
    template = sys.argv[4]
    
    # import the language file
    sys.path.append(os.path.dirname(language))
    import language

    # read the template file
    
    # loop over input message files
    for filename in os.listdir(msgDir):
        file = readFile(msgDir + '/' + filename);
        outputFilename = outDir + "/" + string.split(filename,'.')[0] + '.' + string.split(os.path.basename(template), '.')[1]
        print "outputFilename is " + outputFilename
        # \todo! How to write a try with no except: statements?
        try:
            os.makedirs(os.path.dirname(outputFilename))
        except:
            print ""
        with open(outputFilename,'w') as outFile:
            ProcessFile(file, outFile)
    print ''
