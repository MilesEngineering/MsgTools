#!/usr/bin/env python3
#
# SynchronousMsgClient is a class that contains a TCP client which run asynchronously
# in a background thread, and also allows synchronous code to send and receives messages with it.
#
import os
import sys
import socket

class SynchronousMsgClient:
    def __init__(self, msgLib, name):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 5678))
        self.timeout = 0
        self.msgLib = msgLib
        
        # say my name
        connectMsg = self.msgLib.Messages.Network.Connect()
        connectMsg.SetName(name)
        self.send_message(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = self.msgLib.Messages.Network.MaskedSubscription()
        self.send_message(subscribeMsg)

    def send_message(self, msg):
        self.sock.send(msg.rawBuffer().raw)
    
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
                            msg = self.msgLib.MsgFactory(hdr)
                            return msg
                        #else:
                        #    print("throwing away " + str(id) + " msg")
            except socket.timeout:
                return None

    def stop(self):
        self.sock.close()
