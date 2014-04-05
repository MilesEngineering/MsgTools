#!/usr/bin/python
import sys

def Usage():
    sys.stderr.write('Usage: ' + sys.argv[0] + ' msgdir outputdir language template\n')
    sys.exit(1)

# main starts here
if __name__ == '__main__':
    if len(sys.argv) < 5:
        Usage();

    print 'reading messages from ' + sys.argv[1] + ', writing output to ' + sys.argv[2] + ', using language ' + sys.argv[3] + ', templates ' + sys.argv[4] + '\n';
