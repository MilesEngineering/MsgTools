#!/usr/bin/env python3
#
# SynchronousMsgClient is a class that contains a TCP client which run asynchronously
# in a background thread, and also allows synchronous code to send and receives messages with it.
#
import os
import sys
import socket

class SynchronousMsgClient:
    def __init__(self, hdr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", 5678))
        self.timeout = 0
        self.hdr = hdr
        
    def send_message(self, msg):
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

    
    def get_message(self, timeout, msgIds=[]):
        if self.timeout != timeout:
            self.timeout = timeout
            self.sock.settimeout(self.timeout)
        while True:
            try:
                # see if there's enough for header
                data = self.sock.recv(self.hdr.SIZE, socket.MSG_PEEK)
                if len(data) == self.hdr.SIZE:
                    # read header
                    data = self.sock.recv(self.hdr.SIZE)
                    hdr = self.hdr(data)
                    # read body
                    data += self.sock.recv(hdr.GetDataLength())
                    hdr = self.hdr(data)
                    id = hdr.GetMessageID()
                    if len(msgIds) == 0 or id in msgIds:
                        return hdr
            except socket.timeout:
                return None

    def stop(self):
        self.sock.close()
