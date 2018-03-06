#!/usr/bin/env python3
#
# Creates a SynchronousMsg Client or Server, and uses it for a message console.
# Reads are JSON, writes are CSV.
#
import os
import sys
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

def main(args=None):
    msgLib = Messaging(None, 0, "NetworkHeader")

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
        

    _cmd = ""
    try:
        while True:
            cmd = input("")
            #print("got input cmd [" + cmd + "]")
            if cmd:
                if "getmsg" in cmd:
                    msgIDs = []
                    msgIDNames = cmd.split(",")[1:]
                    for msgname in msgIDNames:
                        try:
                            if int(msgname, 0):
                                msgIDs.append(int(msgname,0))
                        except ValueError:
                            if msgname in Messaging.MsgIDFromName:
                                msgIDs.append(int(Messaging.MsgIDFromName[msgname], 0))
                            else:
                                print("invalid msg " + msgname)
                    # this blocks until message received, or timeout occurs
                    timeout = 10.0 # value in seconds
                    hdr = connection.get_message(timeout, msgIDs)
                    if hdr:
                        msg = msgLib.MsgFactory(hdr)
                        # print as JSON for debug purposes
                        json = Messaging.toJson(msg)
                        print(json)
                    else:
                        print("{}")
                else:
                    # this translates the input command from CSV to a message, and sends it.
                    msg = Messaging.csvToMsg(cmd)
                    if msg:
                        connection.send_message(msg)
    # I can't get exit on Ctrl-C to work!
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
        connection.stop()

if __name__ == "__main__":
    main()
