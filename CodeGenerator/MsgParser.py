#!/usr/bin/env python3
import sys
import os
import string
from time import gmtime, strftime

from MsgUtils import *

def Messages(inputData):
    return inputData["Messages"]

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

# I changed to searching for tags in angle brackets (like <TAG>), and
# looking them up in the replacements hash table (instead of testing
# all tags in the hash table), and saw no performance improvement.
# In fact, application timing doesn't change even if *no* replacements
# are made.  Perhaps timing is dominated by YAML parsing?
def DoReplacements(line, msg, enums, replacements):
    ret = line + '\n'
    for tag in replacements:
        ret = replace(ret, tag, replacements[tag])
    ret = optionalReplace(ret, "<REFLECTION>", 'reflection', msg)
    ret = optionalReplace(ret, "<FIELDINFOS>", 'fieldInfos', msg)
    ret = optionalReplace(ret, "<STRUCTUNPACKING>", 'structUnpacking', msg)
    ret = optionalReplace(ret, "<STRUCTPACKING>", 'structPacking', msg)
    ret = optionalReplace(ret, "<GETMSGID>", 'getMsgID', msg)
    ret = optionalReplace(ret, "<SETMSGID>", 'setMsgID', msg)
    if "<FOREACHFIELD" in ret:
        ret = fieldReplacements(ret, msg)
    if "<FOREACHSUBFIELD" in ret:
        ret = subfieldReplacements(ret, msg)

    # ugly, but do this twice, before and after other replacements, because the code generator
    # might insert it while doing other replacements.
    ret = replace(ret, "<MSGNAME>", replacements["<MSGNAME>"])
    return ret

def CommonSubdir(f1, f2):
    # find largest string shared at end of 2 filenames
    d1 = os.path.dirname(os.path.abspath(f1))
    d2 = os.path.dirname(os.path.abspath(f2))
    minLen = min(len(d1), len(d2))
    subdirComponent = ''
    for i in range(1, minLen):
        if d1[-i] == d2[-i]:
            subdirComponent = d1[-i] + subdirComponent
        else:
            break

    # strip slashes at ends
    return subdirComponent.strip("/")

def ProcessFile(inputFilename, outputFilename, languageFilename, templateFilename):
    commonSubdir = CommonSubdir(inputFilename, outputFilename)
    
    currentDateTime = strftime("%d/%m/%Y at %H:%M:%S")
    
    # read the template file
    with open(templateFilename, 'r') as templateFile:
        template = templateFile.read().splitlines() 
    
    # read the input file
    inputData = readFile(inputFilename)
    try:
        os.makedirs(os.path.dirname(outputFilename))
    except FileExistsError:
        pass
    with open(outputFilename,'w') as outFile:
        try:
            replacements = {}
            enums = Enums(inputData)
            replacements["<ENUMERATIONS>"] = language.enums(enums)
            if "Messages" in inputData:
                for msg in Messages(inputData):
                    replacements["<MSGNAME>"] = msgName(msg)
                    replacements["<NUMBER_OF_FIELDS>"] = str(numberOfFields(msg))
                    replacements["<NUMBER_OF_SUBFIELDS>"] = str(numberOfSubfields(msg))
                    undefinedMsgId = "UNDEFINED_MSGID"
                    try:
                        undefinedMsgId = language.undefinedMsgId()
                    except AttributeError:
                        pass
                    replacements["<MSGID>"] = str(msgID(msg, enums, undefinedMsgId))
                    replacements["<MSGSIZE>"] = str(msgSize(msg))
                    replacements["<MSGDESCRIPTION>"] = str(msg["Description"])
                    replacements["<ACCESSORS>"] = "\n".join(language.accessors(msg))
                    replacements["<DECLARATIONS>"] = "\n".join(language.declarations(msg))
                    replacements["<INIT_CODE>"] = "\n".join(language.initCode(msg))
                    replacements["<OUTPUTFILENAME>"] = outputFilename
                    replacements["<INPUTFILENAME>"] = inputFilename
                    replacements["<TEMPLATEFILENAME>"] = templateFilename
                    replacements["<LANGUAGEFILENAME>"] = languageFilename
                    replacements["<MESSAGE_SUBDIR>"] = commonSubdir
                    replacements["<DATE>"] = currentDateTime
                    for line in template:
                        line = DoReplacements(line, msg, enums, replacements)
                        outFile.write(line)
        except MessageException as e:
            sys.stderr.write(str(e)+'\n')
            outFile.close()
            os.remove(outputFilename)
            sys.exit(1)

def ProcessDir(msgDir, outDir, languageFilename, templateFilename):
    # make the output directory
    try:
        os.makedirs(outDir)
    except:
        pass
    for filename in os.listdir(msgDir):
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            if filename != 'headers':
                try:
                    outputFilename = language.outputSubdir(outDir, filename)
                except AttributeError:
                    outputFilename = outDir + "/" + filename
                ProcessDir(inputFilename, outputFilename, languageFilename, templateFilename)
        else:
            try:
                outputFilename = language.outputFilename(outDir, filename, templateFilename)
            except AttributeError:
                justFilename = filename.split('.')[0] + '.' + os.path.basename(templateFilename).split('.')[1]
                outputFilename = outDir + "/" + justFilename
            inputFileTime = os.path.getmtime(inputFilename)
            try:
                outputFileTime = os.path.getmtime(outputFilename)
            except:
                outputFileTime = 0
            templateFileTime = os.path.getmtime(templateFilename)
            languageFileTime = os.path.getmtime(languageFilename)
            if (inputFileTime > outputFileTime or templateFileTime > outputFileTime or languageFileTime > outputFileTime):
                print("Creating " + outputFilename)
                ProcessFile(inputFilename, outputFilename, languageFilename, templateFilename)

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        sys.stderr.write('Usage: ' + sys.argv[0] + ' input output language template\n')
        sys.exit(1)
    inputFilename = sys.argv[1]
    outputFilename = sys.argv[2]
    languageFilename = sys.argv[3]
    templateFilename = sys.argv[4]

    # import the language file
    sys.path.append(os.path.dirname(languageFilename))
    languageName = os.path.splitext(os.path.basename(languageFilename) )[0]
    language = __import__(languageName)

    if(os.path.isdir(inputFilename)):
        ProcessDir(inputFilename, outputFilename, languageFilename, templateFilename)
    else:
        ProcessFile(inputFilename, outputFilename, languageFilename, templateFilename)
