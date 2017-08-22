import sys
import subprocess
import os
srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")

pythonExe = sys.executable 
codegenDir = "."
msgDir = "../../messages"
objDir = "../../obj/CodeGenerator"
runParser=pythonExe+" "+codegenDir+"/"+"MsgParser.py"
runCheck=pythonExe+" "+codegenDir+"/"+"MsgCheck.py"
digestFile=objDir+'/'+"MsgDigest.txt"

languageOptions = {}
languageOptions['python'] = ["Python", "language.py", "Template.py", "HeaderTemplate.py"]
languageOptions['cpp'] = ["Cpp", "language.py", "CppTemplate.h", "CppHeaderTemplate.h"]
languageOptions['c'] = ["Cpp", "Clanguage.py", "CTemplate.h", "CHeaderTemplate.h"]
languageOptions['java'] = ["Java", "language.py", "JavaTemplate.java", "JavaHeaderTemplate.java"]
languageOptions['js'] = ["Javascript", "language.py", "Template.js", "HeaderTemplate.js"]
languageOptions['matlab'] = ["Matlab", "language.py", "Template.m", "HeaderTemplate.m"]
languageOptions['html'] = ["HTML", "language.py", "Template.html", "HeaderTemplate.html"]
"find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)HTML/bootstrap.min.css"

def build(languageOptions):
    languageDir = languageOptions[0]
    languagePluginName = languageOptions[1]
    template = languageOptions[2]
    headerTemplate = languageOptions[3]
    print("Building " + languageDir)
    invoke = runParser
    invoke += " " + msgDir
    invoke += " "+objDir+"/"+languageDir
    invoke += " "+codegenDir+"/"+languageDir+"/"+languagePluginName
    invoke += " "+codegenDir+"/"+languageDir+"/"+template
    invoke += " "+codegenDir+"/"+languageDir+"/"+headerTemplate
    print(invoke)
    subprocess.call(invoke)

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 1:
        sys.stderr.write('Usage: ' + sys.argv[0] + ' [language]\n')
        sys.stderr.write('[language] is one of python cpp c java js matlab html')
        sys.stderr.write('If unspecified, all languages are built.')
        sys.exit(1)
    try:
        languages = [sys.argv[1]]
    except IndexError:
        languages = "all"
    
    if languages == "all":
        languages = languageOptions.keys()
        
    for language in languages:
        if language == 'check':
            #python.exe MsgCheck.py C:/svn/AD-DataCollection/AD-BmapCommon/obj/CodeGenerator/MsgDigest.txt ../../messages
            invoke = runCheck + " " + digestFile + " " + msgDir
            print(invoke)
            subprocess.call(invoke)
        else:
            build(languageOptions[language])

#clean clobber::
#	rm -rf $(MSGDIR) __pycache__ *.pyc

#check: $(DIGEST)
#$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES))
#	$(call colorecho,Checking message validity)
#	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)
