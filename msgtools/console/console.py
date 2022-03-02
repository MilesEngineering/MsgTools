#!/usr/bin/env python3
#
# Creates a synchronous message Client or Server, and uses it for a message console.
# Reads are JSON, writes are CSV.
#
import os
import sys
import cmd
import traceback
import time
from collections import OrderedDict

from .server import Server
from .client import Client

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging

import msgtools.lib.msgcsv as msgcsv
import msgtools.lib.msgjson as msgjson

class MsgCmd(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = 'msg> '
    def __init__(self, connection, timeout):
        super(MsgCmd, self).__init__()
        self._connection = connection
        self._timeout = timeout
    
    def can_exit(self):
        return True
    def do_exit(self, s):
        print("^D")
        return True
    do_EOF = do_exit

    def do_send(self, line):
        # this translates the input command from CSV to a message, and sends it.
        msg = msgcsv.csvToMsg(line)
        if msg:
            self._connection.send(msg)
            print("sent " + msgcsv.toCsv(msg))
        else:
            print("ERROR! Invalid msg [%s]!" % (line))
    
    def do_recv(self, line):
        msgIDs = []
        msgIDNames = line.split()
        keep_looping = False
        for msgname in msgIDNames:
            if msgname == 'ALL':
                keep_looping = True
                continue
            try:
                if int(msgname, 0):
                    msgIDs.append(int(msgname,0))
            except ValueError:
                if msgname in Messaging.MsgIDFromName:
                    msgIDs.append(int(Messaging.MsgIDFromName[msgname], 0))
                else:
                    print("invalid msg " + msgname)
        if msgIDs:
            msgNames = [Messaging.MsgNameFromID[hex(int(id))] for id in msgIDs]
            print("recv " + str(msgNames))
        else:
            print("recv ANY")
        # this blocks until message received, or timeout occurs
        timeout = self._timeout # value in seconds
        while True:
            try:
                t1 = time.time()
                msg = self._connection.recv(msgIDs, timeout)
                t2 = time.time()
                if timeout != 0.0:
                    delta_t = t2 - t1
                    timeout = timeout - delta_t
                    if timeout < 0:
                        break
            except KeyboardInterrupt:
                msg = None
                print('')
                return
            if msg:
                # print as JSON for debug purposes
                json = msgjson.toJson(msg)
                print(json)
            else:
                print("{}")
            if not keep_looping:
                break
    
    def do_timeout(self, line):
        self._timeout = float(line)
    
    def do_info(self, line):
        try:
            autocomplete, help = msgcsv.csvHelp(line, verbose=True)
            if autocomplete == line or autocomplete == line+",":
                autocomplete, help = msgcsv.csvHelp(line+",", verbose=True)
            if autocomplete and autocomplete.strip() != line.strip():
                print("Invalid message name: " + line)
            elif help:
                print("")
                print(help)
        except:
            print(traceback.format_exc())
        
    def autocomplete(self, commandName, text, line):
        try:
            # get the text with whitespace collapsed, after first word
            simplified = " ".join(line.split()[1:])
            if line.endswith(' ') and len(line.strip()) > len(commandName + " "):
                simplified = simplified + ' '

            autocomplete, help = msgcsv.csvHelp(simplified, verbose= commandName=="info")
            if autocomplete and autocomplete.strip() != simplified.strip():
                return [autocomplete]
            elif help:
                print("")
                print(help)
                print("\n%s%s" % (self.prompt, line), end='')
        except:
            print(traceback.format_exc())
        return []
        
    def complete_send(self, text, line, start_index, end_index):
        return self.autocomplete("send", text, line)

    def complete_recv(self, text, line, start_index, end_index):
        return self.autocomplete("recv", text, line)

    def complete_info(self, text, line, start_index, end_index):
        return self.autocomplete("info", text, line)

def main(args=None):
    Messaging.LoadAllMessages()

    timeout = 10.0
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        connection = Server(timeout)
    else:
        connection = Client("CLI", timeout)
        
    msg_cmd = MsgCmd(connection, timeout)
    try:
        msg_cmd.cmdloop()
    except KeyboardInterrupt:
        print("^C")
        

if __name__ == "__main__":
    main()
