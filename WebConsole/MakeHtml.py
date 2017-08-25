#!/usr/bin/env python3
import sys
import os
import string

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' outputfile msgdir\n')
    sys.exit(1)

def ProcessDir(outFile, msgDir):
    for filename in sorted(os.listdir(msgDir)):
        inputFilename = msgDir + '/' + filename
        if os.path.isdir(inputFilename):
            ProcessDir(outFile, inputFilename)
        elif filename.endswith(".js"):
            script = '<script type="text/javascript" src="%s" ></script>\n' % inputFilename
            outFile.write(script)

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 3:
        Usage();
    outputFilename = sys.argv[1]
    msgDir = sys.argv[2]
    
    global msgNames
    msgNames = {}
    global msgPaths
    msgPaths = {}

    try:
        os.makedirs(os.path.dirname(outputFilename))
    except:
        pass
    with open(outputFilename,'w') as outFile:
        header = \
'''<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8"/>
<!-- Load messaging library -->
<script type="text/javascript" src="../MsgApp/UnknownMsg.js" ></script>
<script type="text/javascript" src="../MsgApp/Messaging.js" ></script>
<!-- Load auto-generated message files. -->
'''
        outFile.write(header)
        ProcessDir(outFile, msgDir)
        footer = \
'''
<!-- Load our main program. -->
<script type="text/javascript" src="%s.js" ></script>
</head>
<body>
  <p>Open debug console to see output of javascript console.log statements!</p>
</body>
</html>''' % outputFilename.split('.')[0]
        outFile.write(footer)
