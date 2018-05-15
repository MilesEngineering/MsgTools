#!/usr/bin/env python3
import os
import sys
import argparse
import jinja2

description = '''This script inspects the given message directory and builds a list of all the message modules
    in the message directory.  It then emits a web app (WebConsole.html) that will load and parse these messages
    to the console.'''


def buildApp(msgdir, outputdir):
    '''We're  just going to iterate each file in the directlry and build a message entry for it.
    Then we'll run Jinja to build a custom web app based on the messages we've processed'''
    if msgdir[len(msgdir) - 1] != os.sep:
        msgdir += os.sep

    messages = []
    dirs = [msgdir]
    while len(dirs) is not 0:
        currentDir = dirs.pop()
        for entry in os.listdir(currentDir):
            currentPath = os.path.join(currentDir, entry)
            if os.path.isdir(currentPath):
                dirs.append(currentPath)
            elif entry.endswith('.js'):
                # Drop the base msgdir and extension
                message = currentPath[
                    0:currentPath.rfind('.')][len(msgdir):]
                message = message.replace(os.sep, '.')
                messages.append(message)
            else:
                print('Skipping {0}; not a Javascript file'.format(
                    currentPath))

    with open('template.html', 'r') as fp:
        html = fp.read()

    # Run the Jinja engine to swap out tags
    template = jinja2.Template(html)
    templateArgs = {}
    templateArgs['msgdir'] = msgdir
    templateArgs['messages'] = messages
    rendering = template.render(**templateArgs)

    with open(outputdir, 'w') as fp:
        fp.write(rendering)

# main starts here
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'outputdir', help='The destination directory for the resulting HTML app')
    parser.add_argument(
        'msgdir', help='The basepath for where generated messages are placed.  For example, obj/CodeGenerator/Javascript')

    args = parser.parse_args()

    if os.path.exists(args.msgdir) is False or os.path.isdir(args.msgdir) is False:
        print('{0} does not exist, or is not a directory'.format(args.msgdir))
        sys.exit(1)

    buildApp(args.msgdir, args.outputdir)
