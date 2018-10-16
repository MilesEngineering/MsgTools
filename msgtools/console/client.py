#!/usr/bin/env python3
#
# Client is a class that contains a TCP client which run asynchronously
# in a background thread, and also allows synchronous code to send and receives messages with it.
#
import os
import sys
import socket
from msgtools.lib.messaging import Messaging

class Client:
    def __init__(self, name='Client', timeout=10):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 5678))
        self.timeout = timeout

        if self.timeout == 0.0:
            self.sock.setblocking(0)
        else:
            self.sock.setblocking(1)
            self.sock.settimeout(self.timeout)

        # say my name
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName(name)
        self.send(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
        self.send(subscribeMsg)
        
    def send(self, msg):
        bufferSize = len(msg.rawBuffer().raw)
        computedSize = msg.hdr.SIZE + msg.hdr.GetDataLength()
        if(computedSize > bufferSize):
            msg.hdr.SetDataLength(bufferSize - msg.hdr.SIZE)
            print("Truncating message to "+str(computedSize)+" bytes")
        if(computedSize < bufferSize):
            # don't send the *whole* message, just a section of it up to the specified length
            self.sock.send(msg.rawBuffer().raw[0:computedSize])
        else:
            self.sock.send(msg.rawBuffer().raw)

    
    def recv(self, msgIds=[], timeout=None):
        # if user didn't pass a list, put the single param into a list
        if not isinstance(msgIds, list):
            msgIds = [msgIds]
        # if they passed classes, get the ID of each
        for i in range(0,len(msgIds)):
            if hasattr(msgIds[i], 'ID'):
                msgIds[i] = msgIds[i].ID
        if timeout != None and self.timeout != timeout:
            self.timeout = timeout
            if self.timeout == 0.0:
                self.sock.setblocking(0)
            else:
                self.sock.setblocking(1)
                self.sock.settimeout(self.timeout)
        while True:
            try:
                # see if there's enough for header
                data = self.sock.recv(Messaging.hdr.SIZE, socket.MSG_PEEK)
                if len(data) == Messaging.hdr.SIZE:
                    # create header based on peek'd data
                    hdr = Messaging.hdr(data)

                    # see if there's enough for the body, too
                    data += self.sock.recv(hdr.GetDataLength(), socket.MSG_PEEK)
                    if len(data) != Messaging.hdr.SIZE + hdr.GetDataLength():
                        print("didn't get whole body, error!")
                        continue

                    # read out what we peek'd.  throw it away because we already peek'd it.
                    junk = self.sock.recv(Messaging.hdr.SIZE + hdr.GetDataLength())

                    # reset the header based on appended data
                    hdr = Messaging.hdr(data)
                    id = hdr.GetMessageID()
                    if len(msgIds) == 0 or id in msgIds:
                        msg = Messaging.MsgFactory(hdr)
                        return msg
            except socket.timeout:
                return None
            except BlockingIOError:
                return None

    def stop(self):
        self.sock.close()
