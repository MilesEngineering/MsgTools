#!/usr/bin/env python3
#
# Client is a class that uses a TCP client socket to allow synchronous code to
# send and receives messages.  All instances of Client share a single TCP socket,
# and can also communicate amongst themselves whether the socket is connected or
# not.
#
import gevent.queue
import gevent.monkey
gevent.monkey.patch_socket()
import os
import sys
import socket
import time
from msgtools.lib.messaging import Messaging
from msgtools.sim.sim_exec import SimExec

class Client:
    # keep a list of all clients, so that when any of them send anything it goes to the others.
    _clients = []
    # One socket, shared by all clients
    # Each client blocks on reading from it's own gevent.queue
    _sock = None
    # A totally separate coroutine does a blocking read with infinite timeout,
    # and writes to all the Client queues.
    _rx_greenlet = None
    # A combined name for all clients
    _name = None
    # record particular messages the user wants to record, even if they never called recv on them
    _extra_msgs_to_record = {}
    received = {}
    def __init__(self, name='Client', timeout=10):
        # keep a reference to Messages, for convenience of cmdline scripts
        self.Messages = Messaging.Messages
        # load all messages if not already loaded
        if Messaging.hdr == None:
            Messaging.LoadAllMessages()

        self._timeout = timeout

        # store combined name
        if Client._name == None:
            Client._name = name
        else:
            Client._name = Client._name + "," + name

        if Client._sock == None and SimExec.allow_socket_comms:
            # if there isn't yet a socket but there should be,
            # call the function to open it.
            Client.reconnect_socket(False)
            # Start a greenlet thread to read from the socket.
            # If the socket closes or has an error, the thread will reconnect it.
            Client._rx_greenlet = gevent.spawn(Client.read_for_all_clients)

        # make a queue for receiving messages from other clients in this
        # same process and from the socket.
        self._rx_queue = gevent.queue.Queue()

        # keep a dictionary of the latest value of all received messages
        self.received = {}
        
        # add us to the list of clients
        Client._clients.append(self)

    @staticmethod
    def reconnect_socket(retry=True):
        if retry:
            # If we're trying to reconnect, wait a little bit so we don't spend
            # a ton of time doing network stuff in the case where the server
            # isn't even running.
            gevent.sleep(0.5)
        try:
            Client._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            Client._sock.connect(("127.0.0.1", 5678))
            Client._sock.setblocking(True)
            Client._sock.settimeout(None)

            # do default subscription to get *everything*
            subscribeMsg = Messaging.Messages.Network.MaskedSubscription()
            Client.static_send(subscribeMsg)

            # Send the connect message with the name
            connectMsg = Messaging.Messages.Network.Connect()
            connectMsg.SetName(Client._name)
            Client.static_send(connectMsg)
        except:
            #print("couldn't open socket!!")
            if not SimExec.sim_exists:
                raise

    @staticmethod
    def static_send(msg):
        if Client._sock == None:
            pass#return

        try:
            bufferSize = len(msg.rawBuffer().raw)
            computedSize = msg.hdr.SIZE + msg.hdr.GetDataLength()
            if(computedSize > bufferSize):
                msg.hdr.SetDataLength(bufferSize - msg.hdr.SIZE)
                print("Truncating message to "+str(computedSize)+" bytes")
            if(computedSize < bufferSize):
                # don't send the *whole* message, just a section of it up to the specified length
                Client._sock.send(msg.rawBuffer().raw[0:computedSize])
            else:
                Client._sock.send(msg.rawBuffer().raw)

        except Exception as e:
            if not SimExec.sim_exists:
                raise
        
    # supposedly it's dangerous for multiple greenlets to send to the same socket!
    #TODO If this causes problems, we'll need to use tx queues to send to a single greenlet,
    #TODO and then have it put data in the socket (like the reverse of how rx works)
    def send(self, msg):
        Client.static_send(msg)
        Client.queue_for_clients(msg, self)

    @staticmethod
    def queue_for_clients(msg, excluded_client):
        if len(Client._clients) > 0:#1:
            for c in Client._clients:
                if c != excluded_client:
                    c._rx_queue.put(msg)

    @staticmethod
    def read_msg_from_socket():
        try:
            # see if there's enough for header
            data = Client._sock.recv(Messaging.hdr.SIZE, socket.MSG_PEEK)
            if len(data) == Messaging.hdr.SIZE:
                # create header based on peek'd data
                hdr = Messaging.hdr(data)

                # see if there's enough for the body, too
                data += Client._sock.recv(hdr.GetDataLength(), socket.MSG_PEEK)
                if len(data) != Messaging.hdr.SIZE + hdr.GetDataLength():
                    #print("didn't get whole body, error!")
                    return None

                # read out what we peek'd.
                data = Client._sock.recv(Messaging.hdr.SIZE + hdr.GetDataLength())

                # reset the header based on appended data
                hdr = Messaging.hdr(data)
                msg = Messaging.MsgFactory(hdr)
                return msg
            else:
                # reopen the socket
                Client.reconnect_socket()
        except ConnectionResetError:
            Client.reconnect_socket()
        except OSError:
            Client.reconnect_socket()
        except socket.timeout:
            print("timeout")
            return None
        except BlockingIOError:
            print('blocking')
            return None
        return None

    @staticmethod
    def read_for_all_clients():
        while True:
            msg = Client.read_msg_from_socket()
            if msg:
                #TODO Should we put everything in the queue?
                #TODO The client might decide to receive a message by ID
                #TODO after it got read from the socket, in which case we'd miss it.
                #TODO That's slightly different than in the single Client version
                #TODO where a Client reads directly from the scoket because then
                #TODO nothing is read from the socket until the Client
                #TODO decides to read and passes a list of msgIds.
                Client.queue_for_clients(msg, None)
            else:
                # If the server disconnects we'll get to this case.
                # That's ok because read_msg_from_socket() will attempt
                # to reconnect.
                pass

    def recv(self, msgIds=[], timeout=None):
        # if user didn't pass a list, put the single param into a list
        if not isinstance(msgIds, list):
            msgIds = [msgIds]
        # if they passed classes, get the ID of each
        for i in range(0,len(msgIds)):
            if hasattr(msgIds[i], 'ID'):
                #print("replacing %s with %s" % (msgIds[i], msgIds[i].ID))
                msgIds[i] = msgIds[i].ID

        # reset the timeout member variable
        if timeout != None and self._timeout != timeout:
            self._timeout = timeout

        if self._timeout == 0.0:
            block = False
            timeout = None
        else:
            block = True
            timeout = self._timeout

        # Process any messages in our rx queue
        while True:
            if block and SimExec.sim_exists:
                # Delay for a period of simulation time, not real time!
                start_time = SimExec.time()
                while True:
                    try:
                        msg = self._rx_queue.get(block=False)
                    except KeyboardInterrupt:
                        raise
                    except:
                        SimExec.tick_event.wait()
                        SimExec.tick_event.clear()
                        if SimExec.time() > start_time + timeout:
                            return None
            else:
                # if we dont't want to block, or else the sim isn't running,
                # then we can read from the queue directly without
                # worrying about simulation time.
                try:
                    msg = self._rx_queue.get(block, timeout)
                except KeyboardInterrupt:
                    raise
                except:
                    return None

            id = msg.hdr.GetMessageID()
            if len(msgIds) == 0 or id in msgIds:
                self.received[id] = msg
                return msg

    def wait_for(self, msgIds=[], fn=None, timeout=None):
        ret = False
        if timeout == None:
            timeout = self._timeout
        remaining_timeout = timeout
        while(1):
            before = SimExec.time()
            msg = self.recv(msgIds, remaining_timeout)
            if msg != None and fn(msg):
                ret = True
                break
            after = SimExec.time()
            elapsed = after - before
            if remaining_timeout:
                # if we have a timeout, update it for the amount of time spent
                remaining_timeout = remaining_timeout - elapsed
                if remaining_timeout < 0:
                    ret = False
                    break
        return ret

    def stop(self):
        Client._clients.remove(self)

    # select set of messages to record the last value of
    def record(self, msgs_to_record):
        Client._extra_msgs_to_record.update(msgs_to_record)
