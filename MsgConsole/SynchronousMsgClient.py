#!/usr/bin/env python3
#
# SynchronousMsgClient is a class that contains a TCP client which run asynchronously
# in a background thread, and also allows synchronous code to send and receives messages with it.
#
import os
import sys
import socket

class SynchronousMsgClient:
    def __init__(self, msgLib):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 5678))
        self.timeout = 0
        self.msgLib = msgLib

    def send_message(self, data):
        self.sock.send(data)
    
    def get_message(self, timeout, msgIds=[]):
        if self.timeout != timeout:
            self.timeout = timeout
            self.sock.settimeout(self.timeout)
        while True:
            try:
                # see if there's enough for header
                data = self.sock.recv(self.msgLib.hdr.SIZE, socket.MSG_PEEK)
                if len(data) == self.msgLib.hdr.SIZE:
                    # read header
                    data = self.sock.recv(self.msgLib.hdr.SIZE)
                    hdr = self.msgLib.hdr(data)
                    # read body
                    data += self.sock.recv(hdr.GetDataLength())
                    if len(msgIds) == 0:
                        return data
                    else:
                        hdr = self.msgLib.hdr(data)
                        id = hdr.GetMessageID()
                        if id in msgIds:
                            return data
                        #else:
                        #    print("throwing away " + str(id) + " msg")
            except socket.timeout:
                return None

    def stop(self):
        self.sock.close()

if __name__ == "__main__":
    # annoying stuff to start Messaging.
    # this should be simpler!
    thisFileDir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(thisFileDir+"/../MsgApp")
    from Messaging import Messaging
    msgLib = Messaging(thisFileDir+"/../../obj/CodeGenerator/Python/", 0, "NetworkHeader")

    server = SynchronousMsgClient()

    _cmd = ""
    try:
        while True:
            cmd = input("")
            #print("got input cmd [" + cmd + "]")
            if cmd:
                if cmd == "getmsg":
                    # this blocks until message received, or timeout occurs
                    timeout = 1 # value in seconds
                    data = server.get_message(timeout, [msgLib.Network.Connect.Connect.ID, msgLib.Debug.AccelData.AccelData.ID])
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
                        server.send_message(msg.rawBuffer().raw)
    # I can't get exit on Ctrl-C to work!
    except KeyboardInterrupt:
        print('You pressed Ctrl+C!')
