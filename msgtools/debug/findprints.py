#!/usr/bin/env python3
import re
import sys
import os
import string
import collections
import hashlib

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' inputdir dictionaryFile dictionaryHeaderFile\n')
    sys.exit(1)

def ProcessDir(inputDir):
    for filename in sorted(os.listdir(inputDir)):
        inputFilename = inputDir + '/' + filename
        if os.path.isdir(inputFilename):
            ProcessDir(inputFilename)
        else:
            if filename.endswith(".h") or filename.endswith(".c") or filename.endswith(".cpp"):
                if filename != "debug_printf.h" and filename != "debug_printf.cpp":
                    #print("reading " + inputFilename)
                    ProcessFile(inputFilename.replace("//", "/"))

def printDictionary(dictFilename, headerFilename):
    md5 = hashlib.md5()
    with open(dictFilename,'w') as dictFile:
        header = \
'''# AUTO-GENERATED FILE, DO NOT HAND EDIT!
# Created by %s
''' % thisInvocation
        dictFile.write(header)
        for formatInfo in dictionary:
            s = str(formatInfo.id) + ": " + formatInfo.formatStr+", "+formatInfo.filename+", " + str(formatInfo.linenumber) + "\n"
            md5.update(s.encode('utf-8'))
            dictFile.write(s)
        md5 = md5.hexdigest()
        dictFile.write("Dictionary md5 is " + md5)

    lineEndings = os.linesep
    # for windows, override lineseperator, to force windows native line endings,
    # even if we're running cygwin with \n line endings.
    if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
        lineEndings="\r\n"

    with open(headerFilename,'w', newline=lineEndings) as hdrFile:
        header = \
'''/* AUTO-GENERATED FILE, DO NOT HAND EDIT!
  Created by %s
  */
''' % thisInvocation
        hdrFile.write(header)
        for formatInfo in dictionary:
            formatStrIdName = formatInfo.filename.replace("/","_").replace(".cpp","").replace(".c","").replace(".","_")+"_line_"+str(formatInfo.linenumber)
            hdrFile.write("#define " + formatStrIdName + " " + str(formatInfo.id)+"\n")
        md5array = "0x" + ", 0x".join([md5[i:i+2] for i in range(0, len(md5), 2)])
        hdrFile.write("#define FORMAT_STR_DICTIONARY_ID " + md5array+"\n")

PrintfInfo = collections.namedtuple('PrintfInfo', ['id', 'formatStr', 'filename', 'linenumber'])

def ProcessFile(inputFilename):
    try:
        escapedFilePath = inputFilename.replace("/","_").replace(".cpp","").replace(".c","").replace(".","_")
        with open(inputFilename, 'r') as inputFile:
            inputData = inputFile.read().splitlines() 
        global maxSubscriptions
        global formatStrId
        lineNumber = 0;
        for line in inputData:
            lineNumber+=1
            formatStr = ""
            try:
                printStatement = ""
                if "#define ESCAPED_FILE_PATH" in line:
                    matchObj = re.search( r'#define\s*ESCAPED_FILE_PATH\s*(.*)', line)
                    escapedFilePathFromFile = matchObj.group(1).strip()
                    if escapedFilePath != escapedFilePathFromFile:
                        print(inputFilename + ":"+str(lineNumber) + ", " + escapedFilePathFromFile + " != " + escapedFilePath)
                        sedCmd = "sed -i '"+str(lineNumber)+"s/"+escapedFilePathFromFile+"/"+escapedFilePath+"/' "+inputFilename
                        #print("need to " + sedCmd)
                        os.system(sedCmd)
                if "debugPrintf(" in line:
                    printStatement = "debugPrintf"
                    matchObj = re.search( r'debugPrintf\(.*("[^"]*")', line)
                    formatStr = matchObj.group(1).strip()
                if "debugWarn(" in line:
                    printStatement = "debugWarn"
                    matchObj = re.search( r'debugWarn\(.*("[^"]*")', line)
                    formatStr = matchObj.group(1).strip()
                if "debugError(" in line:
                    printStatement = "debugError"
                    matchObj = re.search( r'debugError\(.*("[^"]*")', line)
                    formatStr = matchObj.group(1).strip()
                if(formatStr != ""):
                    printInfo = PrintfInfo(formatStrId, formatStr, inputFilename, lineNumber)
                    dictionary.append(printInfo)
                    formatStrId+=1
            except AttributeError:
                print("Regex search error on " + inputFilename + ", line " + str(lineNumber))
                print(line)
                sys.exit(1)
    except UnicodeDecodeError:
        print("UnicodeDecodeError on " + inputFilename) 

def main():
    if len(sys.argv) < 4:
        Usage();
    global thisInvocation
    thisInvocation = " ".join(sys.argv)
    inputDir = sys.argv[1]
    dictionaryFile = sys.argv[2]
    dictionaryHeaderFile = sys.argv[3]

    global dictionary
    dictionary = []
    
    global formatStrId
    formatStrId = 0
    
    ProcessDir(inputDir)

    try:
        os.makedirs(os.path.dirname(dictionaryFile))
    except:
        pass
    printDictionary(dictionaryFile, dictionaryHeaderFile)

# main starts here
if __name__ == '__main__':
    main()
