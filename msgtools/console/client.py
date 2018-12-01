#!/usr/bin/env python3
#
# Client is a class that contains a TCP client which run asynchronously
# in a background thread, and also allows synchronous code to send and receives messages with it.
#
import os
import sys
import socket
import time
from msgtools.lib.messaging import Messaging

class Client:
    def __init__(self, name='Client', timeout=10):
        # keep a reference to Messages, for convenience of cmdline scripts
        self.Messages = Messaging.Messages
        # load all messages if not already loaded
        if Messaging.hdr == None:
            Messaging.LoadAllMessages()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(("127.0.0.1", 5678))
        self._timeout = timeout

        if self._timeout == 0.0:
            self._sock.setblocking(0)
        else:
            self._sock.setblocking(1)
            self._sock.settimeout(self._timeout)

        # say my name
        connectMsg = Messaging.Messages.Network.Connect()
        connectMsg.SetName(name)
        self.send(connectMsg)
        
        # do default subscription to get *everything*
        subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
        self.send(subscribeMsg)
        
        # keep a dictionary of the latest value of all received messages
        self.received = {}
        
        # also record particular messages the user wants to record, even if
        # they never called recv on them
        self._extra_msgs_to_record = {}
    
    def send(self, msg):
        bufferSize = len(msg.rawBuffer().raw)
        computedSize = msg.hdr.SIZE + msg.hdr.GetDataLength()
        if(computedSize > bufferSize):
            msg.hdr.SetDataLength(bufferSize - msg.hdr.SIZE)
            print("Truncating message to "+str(computedSize)+" bytes")
        if(computedSize < bufferSize):
            # don't send the *whole* message, just a section of it up to the specified length
            self._sock.send(msg.rawBuffer().raw[0:computedSize])
        else:
            self._sock.send(msg.rawBuffer().raw)

    
    def recv(self, msgIds=[], timeout=None):
        # if user didn't pass a list, put the single param into a list
        if not isinstance(msgIds, list):
            msgIds = [msgIds]
        # if they passed classes, get the ID of each
        for i in range(0,len(msgIds)):
            if hasattr(msgIds[i], 'ID'):
                msgIds[i] = msgIds[i].ID
        if timeout != None and self._timeout != timeout:
            self._timeout = timeout
            if self._timeout == 0.0:
                self._sock.setblocking(0)
            else:
                self._sock.setblocking(1)
                self._sock.settimeout(self._timeout)
        while True:
            try:
                # see if there's enough for header
                data = self._sock.recv(Messaging.hdr.SIZE, socket.MSG_PEEK)
                if len(data) == Messaging.hdr.SIZE:
                    # create header based on peek'd data
                    hdr = Messaging.hdr(data)

                    # see if there's enough for the body, too
                    data += self._sock.recv(hdr.GetDataLength(), socket.MSG_PEEK)
                    if len(data) != Messaging.hdr.SIZE + hdr.GetDataLength():
                        print("didn't get whole body, error!")
                        continue

                    # read out what we peek'd.
                    data = self._sock.recv(Messaging.hdr.SIZE + hdr.GetDataLength())

                    # reset the header based on appended data
                    hdr = Messaging.hdr(data)
                    id = hdr.GetMessageID()
                    if id in self._extra_msgs_to_record:
                        self.received[id] = msg
                    if len(msgIds) == 0 or id in msgIds:
                        msg = Messaging.MsgFactory(hdr)
                        self.received[id] = msg
                        return msg
            except socket.timeout:
                return None
            except BlockingIOError:
                return None

    def wait_for(self, msgIds=[], fn=None, timeout=None):
        ret = False
        if timeout == None:
            timeout = self._timeout
        remaining_timeout = timeout
        while(1):
            before = time.time()
            msg = self.recv(msgIds, remaining_timeout)
            if msg != None and fn(msg):
                ret = True
                break
            after = time.time()
            elapsed = after - before
            if remaining_timeout:
                # if we have a timeout, update it for the amount of time spent
                remaining_timeout = remaining_timeout - elapsed
                if remaining_timeout < 0:
                    ret = False
                    break
        if timeout:
            self._sock.setblocking(1)
            self._sock.settimeout(self._timeout)
        return ret

    def stop(self):
        self._sock.close()

    # select set of messages to record the last value of
    def record(self, msgs_to_record):
        self._extra_msgs_to_record = msgs_to_record
