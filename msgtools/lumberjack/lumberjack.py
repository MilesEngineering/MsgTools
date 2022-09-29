#!/usr/bin/env python3
import json
import sys
import os
import argparse

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)

from msgtools.lib.file_reader import MessageFileReader
from msgtools.lib.messaging import Messaging
import msgtools.lib.msgcsv as msgcsv
import msgtools.lib.msgjson as msgjson

DESCRIPTION='''
    Lumberjack creates either a subdirectory with one CSV file per message type received in that directory,
    or a single JSON file if --json is specified.
'''
class Lumberjack(MessageFileReader):
    def __init__(self):
        super(Lumberjack, self).__init__()

        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('-o', '--outputdir', help='''Specifies the name of the directory to output
            parsed data to.  Required for non-file connectionTypes.''')
        parser.add_argument('logfile', help='''The log file you want to split into CSV.  
            .log extension assumes the log is binary with NetworkHeaders.  A .txt extension assumes the 
            file was created with SerialHeaders.''')
        parser.add_argument('--json', action='store_true', help='''Causes output to go to a single JSON file instead of a directory of CSV files.''')
        parser.add_argument('--serial', action='store_true', help='''Assumes input file contains binary messages with SerialHeaders instead of NetworkHeaders.''')
        self.args = parser.parse_args()

        if self.args.logfile.lower().endswith('.txt'):
            self.args.serial = True

        # If the user specified the output dir use it.  If the user 
        # specified a source file, then figure out the output dir
        # from the source filename
        if self.args.outputdir is not None:
            self.output_name = self.args.outputdir
        else:
            self.output_name = self.args.logfile.replace('.bin', '')
            self.output_name = self.output_name.replace('.log', '')
            self.output_name = self.output_name.replace('.txt', '')
            self.output_name = self.output_name.replace('.TXT', '')

        if self.args.json:
            self.output_name = self.output_name + ".json"
        else:
            if os.path.exists(self.output_name) is False:
                os.makedirs(self.output_name)
        print("Writing output to " + self.output_name + "\n")

        if self.args.json:
            self.output_file = open(self.output_name, 'w')
        else:
            self.output_files = {}

        self.message_count = 0

        header_name = "NetworkHeader"
        if self.args.serial:
            header_name = "SerialHeader"
        self.read_file(self.args.logfile, header_name)

    def process_message(self, msg, timestamp):
        self.message_count += 1
        
        id = msg.hdr.GetMessageID()

        if self.args.json:
            output_file = self.output_file
        else:
            # if we write CSV to multiple files, we'd probably look up a hash table for this message id,
            # and open it and write a header
            if(id in self.output_files):
                output_file = self.output_files[id]
            else:
                # create a new file
                output_file = open(self.output_name + "/" + msg.MsgName().replace("/","_") + ".csv", 'w')

                # store a pointer to it, so we can find it next time (instead of creating it again)
                self.output_files[id] = output_file
                
                # add table header, one column for each message field
                tableHeader = msgcsv.csvHeader(msg, nameColumn=False, timeColumn=True) + '\n'
                output_file.write(tableHeader)

        if self.args.json:
            # Get a dictionary of the message
            dict = msg.toDict(includeHeader=True)

            # the dict has one key, which is the name of the message
            msgname = list(dict.keys())[0]

            # Within the value for that key, there's a "hdr", which contains "Time",
            # and we should override that with the corrected timestamp
            dict[msgname]['hdr']['Time'] = timestamp

            text = json.dumps(dict) + '\n'
            output_file.write(text)
        else:
            text = str(timestamp) + ", "
            text += msgcsv.toCsv(msg, nameColumn=False, timeColumn=False)
            text += '\n'
            output_file.write(text)

def main():
    lumberjack = Lumberjack()

    print("Processed %d messages" % (lumberjack.message_count))

# main starts here
if __name__ == '__main__':
    main()
