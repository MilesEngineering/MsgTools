#!/usr/bin/env python3
#
# Creates a SynchronousMsg Client or Server, and uses it for a message console.
# Reads are JSON, writes are CSV.
#
# based on:
#   https://stackoverflow.com/questions/29324610/python-queue-linking-object-running-asyncio-coroutines-with-main-thread-input
#   https://stackoverflow.com/questions/32054066/python-how-to-run-multiple-coroutines-concurrently-using-asyncio
#   https://websockets.readthedocs.io/en/stable/intro.html
import os
import sys
from SynchronousMsgServer import SynchronousMsgServer
from SynchronousMsgClient import SynchronousMsgClient

if __name__ == "__main__":
    # annoying stuff to start Messaging.
    # this should be simpler!
    thisFileDir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(thisFileDir+"/../MsgApp")
    from Messaging import Messaging
    msgLib = Messaging(thisFileDir+"/../../obj/CodeGenerator/Python/", 0, "NetworkHeader")

    if len(sys.argv) > 1 and sys.argv[1] == "client":
        connection = SynchronousMsgClient(msgLib)
    else:
        connection = SynchronousMsgServer(msgLib)

    _cmd = ""
    try:
        while True:
            cmd = input("")
            #print("got input cmd [" + cmd + "]")
            if cmd:
                if cmd == "getmsg":
                    # this blocks until message received, or timeout occurs
                    timeout = 10.0 # value in seconds
                    data = connection.get_message(timeout, [msgLib.Network.Connect.Connect.ID, msgLib.Debug.AccelData.AccelData.ID])
                    if data:
                        # print as JSON for debug purposes
                        hdr = Messaging.hdr(data)
                        msg = Messaging.MsgFactory(hdr)
                        json = Messaging.toJson(msg)
                        print(json)
                    else:
                        print("{}")
                else:
                    # this translates the input command from CSV to a message, and sends it.
                    msg = Messaging.csvToMsg(cmd)
                    if msg:
                        connection.send_message(msg.rawBuffer().raw)
    # I can't get exit on Ctrl-C to work!
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
        connection.stop()
