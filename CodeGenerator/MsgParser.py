#!/usr/bin/python
import sys
import yaml
import json
import os
import io

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

def printMessage(msg):
    print msg["Name"] + ": " + msg["Description"]
    for field in msg["Fields"]:
        print field["Name"] + ": " + field["Type"]

def Messages(file):
    return file["Messages"]

def Enums(file):
    return file["Enums"]

def ProcessFile(file):
    if "Enums" in file:
        for enum in Enums(file):
            print "Enum " + enum["Name"] + ":"
            for option in enum["Options"]:
                print "    " + option["Name"] + " = " + str(option["Value"])
        print ""
    for msg in Messages(file):
        printMessage(msg)
    
# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        Usage();
    msgDir = sys.argv[1]
    outDir = sys.argv[2]
    language = sys.argv[3]
    template = sys.argv[4]
    
    # import the language file
    
    # read the template file
    
    # loop over input message files
    for filename in os.listdir(msgDir):
        file = readFile(msgDir + '/' + filename);
        ProcessFile(file)
    print ''
