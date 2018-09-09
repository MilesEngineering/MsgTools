#!/usr/bin/env python3
#
# Creates a SynchronousMsg Client or Server, and uses it for a message console.
# Reads are JSON, writes are CSV.
#
import os
import sys
import cmd
import traceback
from collections import OrderedDict

from .SynchronousMsgServer import SynchronousMsgServer
from .SynchronousMsgClient import SynchronousMsgClient

# annoying stuff to start Messaging.
# this should be simpler!
try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
    from msgtools.lib.messaging import Messaging

class MsgCmd(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = 'msg> '
    def __init__(self, connection):
        super(MsgCmd, self).__init__()
        self._connection = connection

    def do_send(self, line):
        # this translates the input command from CSV to a message, and sends it.
        msg = Messaging.csvToMsg(line)
        if msg:
            self._connection.send_message(msg)
            print("sent " + msg.MsgName() + " " + Messaging.toCsv(msg))
        else:
            print("ERROR! Invalid msg [%s]!" % (line))
    
    def do_recv(self, line):
        msgIDs = []
        msgIDNames = line.split()
        for msgname in msgIDNames:
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
            print("recv ALL")
        # this blocks until message received, or timeout occurs
        timeout = 10.0 # value in seconds
        try:
            hdr = self._connection.get_message(timeout, msgIDs)
        except KeyboardInterrupt:
            hdr = None
        if hdr:
            msg = Messaging.MsgFactory(hdr)
            # print as JSON for debug purposes
            json = Messaging.toJson(msg)
            print(json)
        else:
            print("{}")

    def autocomplete(self, commandName, text, line, completeparams):
        try:
            if completeparams:
                # get the text with whitespace collapsed, after first word
                simplified = " ".join(line.split()[1:])
                if line.endswith(' ') and len(line.strip()) > len(commandName + " "):
                    simplified = simplified + ' '
            else:
                # use last word
                simplified = text

            autocomplete, help = Messaging.csvHelp(simplified)
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
        return self.autocomplete("send", text, line, True)

    def complete_recv(self, text, line, start_index, end_index):
        return self.autocomplete("recv", text, line, False)

def main(args=None):
    msgLib = Messaging()

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        connection = SynchronousMsgServer(Messaging.hdr)
    else:
        connection = SynchronousMsgClient(Messaging.hdr)
        # say my name
        connectMsg = msgLib.Messages.Network.Connect()
        connectMsg.SetName("CLI")
        connection.send_message(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = msgLib.Messages.Network.MaskedSubscription()
        connection.send_message(subscribeMsg)
        
    msg_cmd = MsgCmd(connection)
    try:
        msg_cmd.cmdloop()
    except KeyboardInterrupt:
        print("exit")
        

if __name__ == "__main__":
    main()
