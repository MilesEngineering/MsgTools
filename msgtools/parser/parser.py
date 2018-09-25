#!/usr/bin/env python3
import sys
import os
import string
import argparse
import pkg_resources

from time import gmtime, strftime

DESCRIPTION = '''Applies message and header language template files to
                 YAML message inputs to generate code for creating
                 and parsing messages.  Header definitions are assumed 
                 to reside in a folder called headers at the root of the input 
                 directory.  A header called NetworkHeader.yaml MUST
                 be defined, and adhere to the contract outlined in 
                 the test message suite.'''

EPILOG = '''Built-in languages have precedence over plugins.  If your plugin
            uses the same name as a built-in language, it will be ignored.'''

# Used to find the default template and header template within the language 
# folder. These are case sensitive.
DEFAULT_TEMPLATE = 'Template.'
DEFAULT_HEADER_TEMPLATE = 'HeaderTemplate.'

try:
    from msgtools.parser.MsgUtils import *
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.parser.MsgUtils import *

def Messages(inputData):
    return inputData["Messages"]

def replace(line, pattern, replacement):
    if pattern in line:
        ret = ""
        if replacement != "":
            #print("replacing ", pattern, " with ", replacement)
            for newLine in replacement.split('\n'):
                ret += line.replace(pattern, newLine)
    else:
        # print("NOT replacing ", pattern, " with ", replacement, " in ", line)
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
def DoReplacements(line, msg, replacements, firstTime):
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
    ret = replace(ret, "<MSGSHORTNAME>", replacements["<MSGSHORTNAME>"])
    if "<ONCE>" in ret:
        if firstTime:
            ret = ret.replace("<ONCE>", "")
        else:
            ret = ""
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
    return subdirComponent.strip("/").strip("\\")

def OutputFile(inputFilename, inputName, outDir):
    try:
        outputFilename = language.outputFilename(outDir, inputName, templateFilename)
    except AttributeError:
        justFilename = inputName + '.' + os.path.basename(templateFilename).split('.')[1]
        outputFilename = outDir + "/" + justFilename
    inputFileTime = os.path.getmtime(inputFilename)
    try:
        outputFileTime = os.path.getmtime(outputFilename)
    except:
        outputFileTime = 0
    try:
        templateFileTime = os.path.getmtime(templateFilename)
    except:
        templateFileTime = 0
    try:
        languageFileTime = os.path.getmtime(languageFilename)
    except:
        languageFileTime = 0
    if (inputFileTime > outputFileTime or templateFileTime > outputFileTime or languageFileTime > outputFileTime):
        try:
            os.makedirs(os.path.dirname(outputFilename))
        except FileExistsError:
            pass
        lineEndings = os.linesep
        # for windows, override lineseperator, to force windows native line endings,
        # even if we're running cygwin with \n line endings.
        if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
            lineEndings="\r\n"
        print("Creating " + outputFilename)
        return outputFilename, open(outputFilename,'w', newline=lineEndings)
    return outputFilename, None

def ProcessFile(inputFilename, outDir, languageFilename, templateFilename, messaging):
    currentDateTime = strftime("%d/%m/%Y at %H:%M:%S")
    
    try:
        oneOutputFilePerMsg = language.oneOutputFilePerMsg
    except AttributeError:
        oneOutputFilePerMsg = False
        
    # open output file now
    if not oneOutputFilePerMsg:
        filename = os.path.basename(inputFilename).split('.')[0]
        outputFilename, outFile = OutputFile(inputFilename, filename, outDir)
        if not outFile:
            return

    # read the input file
    inputData = readFile(inputFilename)

    # if there's no input, return without creating output
    if inputData == 0:
        return

    # read the template file
    if os.path.isfile(templateFilename):
        with open(templateFilename, 'r') as templateFile:
            template = templateFile.read().splitlines()
    elif os.path.isfile(languageFilename+'/'+templateFilename):
        with open(languageFilename+'/'+templateFilename, 'r') as templateFile:
            template = templateFile.read().splitlines()
    else:
        from pkg_resources import resource_string
        try:
            template = resource_string(language.__name__, templateFilename).decode('UTF-8', 'replace').splitlines()
        except FileNotFoundError:
            print("Error opening " + language.__name__ + " " + templateFilename)
            sys.exit(1)
    
    replacements = {}
    enums = Enums(inputData)
    ids = MsgIDs(inputData)
    
    PatchStructs(inputData)
    
    firstTime = True
    if "Messages" in inputData:
        for msg in Messages(inputData):
            msg["ids"] = ids
            try:
                msg["commonSubdir"] = CommonSubdir(inputFilename, outDir+"/fake")

                if oneOutputFilePerMsg:
                    outputFilename, outFile = OutputFile(inputFilename, msgShortName(msg), outDir)
                    if not outFile:
                        continue

                replacements["<MESSAGINGMODULE>"] = messaging
                replacements["<ENUMERATIONS>"] = language.enums(UsedEnums(msg, enums))
                replacements["<MSGNAME>"] = msgName(msg)
                replacements["<MSGSHORTNAME>"] = msgShortName(msg)
                replacements["<NUMBER_OF_FIELDS>"] = str(numberOfFields(msg))
                replacements["<NUMBER_OF_SUBFIELDS>"] = str(numberOfSubfields(msg))
                undefinedMsgId = "UNDEFINED_MSGID"
                try:
                    undefinedMsgId = language.undefinedMsgId()
                except AttributeError:
                    pass
                try:
                    replacements["<MSGID>"] = language.languageConst(msgID(msg, enums, undefinedMsgId))
                except AttributeError:
                    replacements["<MSGID>"] = str(msgID(msg, enums, undefinedMsgId))
                replacements["<MSGSIZE>"] = str(msgSize(msg))
                replacements["<MSGDESCRIPTION>"] = str(fieldItem(msg, "Description", "")).replace('\n', ' ')
                replacements["<ACCESSORS>"] = "\n".join(language.accessors(msg))
                replacements["<DECLARATIONS>"] = "\n".join(language.declarations(msg))
                replacements["<INIT_CODE>"] = "\n".join(language.initCode(msg))
                replacements["<OUTPUTFILENAME>"] = outputFilename
                replacements["<INPUTFILENAME>"] = inputFilename
                replacements["<TEMPLATEFILENAME>"] = templateFilename
                replacements["<LANGUAGEFILENAME>"] = languageFilename
                replacements["<MESSAGE_PACKAGE>"] = msg["commonSubdir"].replace( '/', '.').replace( '\\', '.')
                replacements["<MSGDESCRIPTOR>"] = msgDescriptor(msg, inputFilename)
                replacements["<DATE>"] = currentDateTime
                replacements["<MSGALIAS>"] = msgAlias(msg)
                for line in template:
                    line = DoReplacements(line, msg, replacements, firstTime)
                    outFile.write(line)
                if oneOutputFilePerMsg:
                    outfileLen = outFile.tell()
                    outFile.close()
                    # It's possible to have empty files as some YAML files can serve as a pure base 
                    # for others that never generate code.  Clean up empty files
                    if outfileLen == 0:
                        os.remove(outputFilename)
                else:
                    firstTime = False

            except MessageException as e:
                sys.stderr.write(str(e)+'\n')
                outFile.close()
                os.remove(outputFilename)
                sys.exit(1)
    if not oneOutputFilePerMsg:
        outfileLen = outFile.tell()
        outFile.close()
        if outfileLen == 0:
            # It's possible to have empty files as some YAML files can serve as a pure base 
            # for others that never generate code.  Clean up empty files
            os.remove(outputFilename)

def ProcessDir(msgDir, outDir, languageFilename, templateFilename, headerTemplateFilename, messaging):
    # make the output directory
    try:
        os.makedirs(outDir)

        # Make sure we have __init__.py to make Python2 imports happy
        open(os.path.join(outDir, '__init__.py'), 'at').close()
    except:
        pass
    for filename in os.listdir(msgDir):
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            try:
                subdir = language.outputSubdir(outDir, filename)
            except AttributeError:
                subdir = outDir + "/" + filename
            ProcessDir(inputFilename, subdir, languageFilename, templateFilename, headerTemplateFilename, messaging)
        else:
            particularTemplate = templateFilename
            if msgDir.endswith("headers"):
                particularTemplate = headerTemplateFilename
            if filename.endswith(".yaml") or filename.endswith(".json"):
                ProcessFile(inputFilename, outDir, languageFilename, particularTemplate, messaging)

def getAvailableLanguages():
    '''Look at all supported languages.  Assume each language is a 
    subdirectory of the parser.  Special omission of python
    cache and test directories'''
    languageDir = os.path.dirname(os.path.realpath(__file__)) + "/"

    # Use a set - thep plugin could duplicate a built-in language
    languages = set()
    for file in os.listdir(languageDir):
        fullpath = os.path.join(languageDir, file)
        if file != '__pycache__' and file != 'test' and os.path.isdir(fullpath):
            languages.add(file)

    # Discovery plugin entry points
    for entry_point in pkg_resources.iter_entry_points("msgtools.parser.plugin"):
        languages.add(entry_point.name)

    languages = list(languages)
    languages.sort()

    return languages

def loadlanguage(languageName):
    # assume the languageName is a subdirectory of the parser's location,
    # and try loading a language from there
    languageDir = os.path.dirname(os.path.realpath(__file__)) + "/" + languageFilename
    if os.path.isdir(languageDir):
        sys.path.append(os.path.abspath(languageDir))
        return __import__('language')
    # if the above fails, iterate over packages that implement the plugin interface
    import pkg_resources
    for entry_point in pkg_resources.iter_entry_points("msgtools.parser.plugin"):
        if entry_point.name == languageFilename:
            return entry_point.load()
    print("Error loading plugin " + languageName)
    sys.exit(1)

def getTemplate(language, templateBase):
    '''Search the given language sub-folder for the template.
    Basically we are looking for specific filename, with an extension
    appropriate to the language we're processing'''

    for file in os.listdir(os.path.dirname(os.path.realpath(__file__)) + "/" + language):
        index = file.rfind(templateBase)
        if index == 0:
            return file[index:]

    print('Unable to find template base "{0}"" for language {1}'.format(templateBase, language))

def main():

    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
    parser.add_argument('input', help='YAML base directory, or a specific YAML file you want to process.')
    parser.add_argument('output', help='Destination directory for generated language files.')
    parser.add_argument('language', choices=getAvailableLanguages(), help='''Language to target.  
        This includes built-in and plugin laguages.''')
    parser.add_argument('-t', '--template', dest='template',
        help='Message template to use for messages.  If unspecified defaults to the template provided by MsgTools')
    parser.add_argument('-m', '--messaging', dest='messaging', default='msgtools.lib.messaging',
        help='''Messaging module to use for message registration in the templates.  Default is msgtool.lib.messaging.
            You can use this argument to provide a custom messaging module of your own if desired.''')
    parser.add_argument('-ht', '--headertemplate', dest='headertemplate', 
        help='''Header template applied to messages in the "headers" folder.  If unspecified defaults to the 
                template provided by MsgTools.''')
    args = parser.parse_args()
  
    global inputFilename, outputFilename, languageFilename, templateFilename, headerTemplateFilename
    inputFilename = args.input
    outputFilename = args.output
    languageFilename = args.language
    templateFilename = args.template
    headerTemplateFilename = args.headertemplate

    # import the language file
    global language
    language = loadlanguage(languageFilename)

    # If this is a plugin the -t and -ht arguments are no longer optional
    if args.language == 'plugin'and (args.template is None or args.headertemplate  is None):
        print('You must specify both templates for plugins')
        sys.exit(1)

    # If the user didn't specify a template or header template then
    # use the language defaults
    if templateFilename is None:
        templateFilename = getTemplate(languageFilename, DEFAULT_TEMPLATE)
    if headerTemplateFilename is None:
        headerTemplateFilename = getTemplate(languageFilename, DEFAULT_HEADER_TEMPLATE)
    
    if(os.path.exists(inputFilename)):
        if(os.path.isdir(inputFilename)):
            ProcessDir(inputFilename, outputFilename, languageFilename, templateFilename, headerTemplateFilename, args.messaging)
        else:
            particularTemplate = templateFilename
            if "/headers/" in outputFilename:
                particularTemplate = headerTemplateFilename
            ProcessFile(inputFilename, outputFilename, languageFilename, particularTemplate, args.messaging)
    else:
        print("Path " + inputFilename + " does not exist!")


# main starts here
if __name__ == '__main__':
    main()
