#!/usr/bin/env python3
import collections
import hashlib
import json
import os
import re
import sys
import string
import shutil

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

def theSameWithoutComments(file1, file2):
    with open(file1) as text1, open(file2) as text2:
        if [line for line in text1 if not line.startswith('#')] == [line for line in text2 if not line.startswith('#')]:
            return True
    return False
    
def printDictionary(dictFilename, headerFilename, dictionaryDeployDir):
    # Read in the old dictionary file so we can compare it to new desired
    # contents, to decide if we need to rewrite it.
    try:
        with open(dictFilename, 'r') as file:
            old_file_contents = file.read()
    except:
        old_file_contents = ""
    new_file_contents = ""
    md5 = hashlib.md5()
    header = \
'''# AUTO-GENERATED FILE, DO NOT HAND EDIT!
# Created by %s
''' % thisInvocation
    new_file_contents += header
    for formatInfo in dictionary:
        s = json.dumps(formatInfo.to_dict())+"\n"
        #s = str(formatInfo.id) + ": " + formatInfo.format_str+", "+formatInfo.filename+", " + str(formatInfo.linenumber) + "\n"
        md5.update(s.encode('utf-8'))
        new_file_contents += s
    md5 = md5.hexdigest()
    new_file_contents += "# Dictionary md5 is %s\n" % (md5)

    # Only write the file if the contents changed.
    if new_file_contents != old_file_contents:
        with open(dictFilename,'w') as dictFile:
            dictFile.write(new_file_contents)
    
    # copy the dictionary file to the deploy directory
    if dictionaryDeployDir != None:
        deployedFile = "%s/%s.json" % (dictionaryDeployDir,md5)
        if os.path.isfile(deployedFile):
            if not theSameWithoutComments(dictFilename, deployedFile):
                raise ValueError("ERROR!  Files %s and %s exist but are not identical!!" % (dictFilename, deployedFile))
        shutil.copy2(dictFilename, deployedFile)


    # Read in the old dictionary header file so we can compare it to new
    # desired contents, to decide if we need to rewrite it.
    try:
        with open(headerFilename, 'r') as file:
            old_file_contents = file.read()
    except:
        old_file_contents = ""
    new_file_contents = ""

    lineEndings = os.linesep
    # for windows, override lineseperator, to force windows native line endings,
    # even if we're running cygwin with \n line endings.
    if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
        lineEndings="\r\n"

    header = \
'''/* AUTO-GENERATED FILE, DO NOT HAND EDIT!
Created by %s
*/
''' % thisInvocation
    new_file_contents += header
    for formatInfo in dictionary:
        format_str_id_name = formatInfo.filename.replace("/","_").replace(".cpp","").replace(".c","").replace(".","_")+"_line_"+str(formatInfo.linenumber)
        new_file_contents += "#define %s %d\n" % (format_str_id_name, formatInfo.id)
        new_file_contents +="#define %s_PARAM_TYPE_BITMASK 0x%X\n" % (format_str_id_name, formatInfo.param_type_bitmask)
    md5array = "0x" + ", 0x".join([md5[i:i+2] for i in range(0, len(md5), 2)])
    new_file_contents +="#define FORMAT_STR_DICTIONARY_ID %s\n" % (md5array)

    # Only write the file if the contents changed.
    # This prevents changes to source code from regenerating the dictionary
    # file and changing it's timestamp unless it actually changed, so that
    # we won't needlessly recompile code that depends on it.
    if new_file_contents != old_file_contents:
        print("Contents changed, regenerating %s" % (headerFilename))
        with open(headerFilename,'w', newline=lineEndings) as hdrFile:
            hdrFile.write(new_file_contents)
    else:
        print("Contents haven't changed, not regenerating %s" % (headerFilename))

def format_specifier_list(format_str):
    return re.findall(r'%[0-9\.lh]*[cdeEfgGiuopsxX%]', format_str)

def param_type_bitmask(format_str):
    bitmask = 0
    format_specifiers = format_specifier_list(format_str)
    for format_specifier in format_specifiers:
        bitmask <<= 1
        if 'f' in format_specifier:
            bitmask |= 1
    return bitmask

inttypes_format_specifiers = {
    "PRId8": "d",
    "PRId16": "d",
    "PRId32": "d",
    "PRId64": "ld",
    "PRId64": "lld",
    "PRIi8": "i",
    "PRIi16": "i",
    "PRIi32": "i",
    "PRIi64": "li",
    "PRIi64": "lli",
    "PRIo8": "o",
    "PRIo16": "o",
    "PRIo32": "o",
    "PRIo64": "lo",
    "PRIo64": "llo",
    "PRIx8": "x",
    "PRIx16": "x",
    "PRIx32": "x",
    "PRIx64": "lx",
    "PRIx64": "llx",
    "PRIX8": "X",
    "PRIX16": "X",
    "PRIX32": "X",
    "PRIX64": "lX",
    "PRIX64": "llX",
    "PRIu8": "u",
    "PRIu16": "u",
    "PRIu32": "u",
    "PRIu64": "lu",
    "PRIu64": "llu"
}

class PrintfInfo:
    def __init__(self, id, format_str, filename, linenumber):
        self.id = id
        self.filename = filename
        self.linenumber = linenumber
        self.param_type_bitmask = param_type_bitmask(format_str)
        # replace inttypes format specifiers
        while '" PRI' in format_str:
            matchObj = re.search( r'.*" (.*) ".*', format_str)
            specifier = matchObj.group(1).strip()
            conversion = inttypes_format_specifiers[specifier]
            format_str = format_str.replace('" %s "' % specifier, conversion)
        self.format_str = format_str
    def to_dict(self):
        ret = {}
        ret['id'] = self.id
        ret['format'] = self.format_str
        ret['filename'] = self.filename
        ret['linenumber'] = self.linenumber
        ret['type_bitmask'] = self.param_type_bitmask
        return ret

def ProcessFile(inputFilename):
    try:
        escapedFilePath = inputFilename.replace("/","_").replace(".cpp","").replace(".c","").replace(".","_")
        with open(inputFilename, 'r') as inputFile:
            inputData = inputFile.read().splitlines() 
        global maxSubscriptions
        global format_str_id
        lineNumber = 0;
        for line in inputData:
            lineNumber+=1
            format_str = ""
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
                elif "debugPrintf(" in line:
                    printStatement = "debugPrintf"
                    matchObj = re.search( r'debugPrintf\("(.*)"', line)
                    format_str = matchObj.group(1).strip()
                elif "debugWarn(" in line:
                    printStatement = "debugWarn"
                    matchObj = re.search( r'debugWarn\("(.*)"', line)
                    format_str = matchObj.group(1).strip()
                elif "debugError(" in line:
                    printStatement = "debugError"
                    matchObj = re.search( r'debugError\("(.*)"', line)
                    format_str = matchObj.group(1).strip()
                if format_str != "":
                    printInfo = PrintfInfo(format_str_id, format_str, inputFilename, lineNumber)
                    dictionary.append(printInfo)
                    format_str_id+=1
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
    try:
        dictionaryDeployDir = sys.argv[4]
    except IndexError:
        dictionaryDeployDir = None

    global dictionary
    dictionary = []
    
    global format_str_id
    format_str_id = 0
    
    inputDirList = inputDir.split(',')
    for d in inputDirList:
        ProcessDir(d)

    try:
        os.makedirs(os.path.dirname(dictionaryFile))
    except:
        pass
    printDictionary(dictionaryFile, dictionaryHeaderFile, dictionaryDeployDir)

# main starts here
if __name__ == '__main__':
    main()
