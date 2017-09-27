#!/usr/bin/env python3
# based on:
#   https://stackoverflow.com/questions/29324610/python-queue-linking-object-running-asyncio-coroutines-with-main-thread-input
#   https://stackoverflow.com/questions/32054066/python-how-to-run-multiple-coroutines-concurrently-using-asyncio
#   https://websockets.readthedocs.io/en/stable/intro.html
import os
import sys
import asyncio
import websockets
import janus
import signal

loop = asyncio.get_event_loop()
msg_q = janus.Queue(loop=loop)

async def handle_tcp_client(client_reader):
    #print("handle_tcp_client")
    while True:
        # we *should* read Messaging.hdr.SIZE bytes,
        # then parse header to see body length,
        # then read those bytes.
        data = await client_reader.read(1024)
        if not data:
            break
        hdr = Messaging.hdr(data)
        msg = Messaging.MsgFactory(hdr)
        json = Messaging.toJson(msg)
        print(json)

async def get_msg():
  loop = asyncio.get_event_loop()
  return (await msg_q.async_q.get())

def csvToMsg(lineOfText):
    firstWord = lineOfText.split()[0]
    if firstWord in Messaging.MsgClassFromName:
        msgClass = Messaging.MsgClassFromName[firstWord]
        msg = msgClass()
        if msg.fields:
            paramString = lineOfText.replace(firstWord, "",1)
            params = paramString.split(',')
            try:
                paramNumber = 0
                for fieldInfo in msgClass.fields:
                    if(fieldInfo.count == 1):
                        if len(fieldInfo.bitfieldInfo) == 0:
                            Messaging.set(msg, fieldInfo, params[paramNumber])
                            paramNumber+=1
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                Messaging.set(msg, bitInfo, params[paramNumber])
                                paramNumber+=1
                    else:
                        arrayList = []
                        for i in range(0,fieldInfo.count):
                            Messaging.set(msg, fieldInfo, params[paramNumber], i)
                            paramNumber+=1
            except IndexError:
                # if index error occurs on accessing params, then stop processing params
                # because we've processed them all
                pass
        return msg
    else:
        print("["+lineOfText+"] is NOT A MESSAGE NAME!")
    return None

tcp_clients = {} # task -> (reader, writer)
ws_clients = []

def client_connected_handler(client_reader, client_writer):
    # Start a new asyncio.Task to handle this specific client connection
    task = asyncio.Task(handle_tcp_client(client_reader))
    print("Added new client to list of " + str(len(tcp_clients)) + " clients")
    tcp_clients[task] = (client_reader, client_writer)

    def client_done(task):
        print("client exited")
        # When the tasks that handles the specific client connection is done
        del tcp_clients[task]

    # Add the client_done callback to be run when the future becomes done
    task.add_done_callback(client_done)

async def handle_console_input():
    while True:
        msg = await get_msg()
        # send to TCP clients
        for task in tcp_clients.keys():
            (reader, writer) = tcp_clients[task]
            #print('sending console io msg to client')
            #yield client.send(msg.rawBuffer().raw)
            writer.write(msg.rawBuffer().raw)
        
        # send to Websocket clients
        for ws in ws_clients:
            await ws.send(msg.rawBuffer().raw)

async def handle_ws_client(websocket, path):
    while True:
        ws_clients.append(websocket)
        data = await websocket.recv()
        if not data:
            break
        hdr = Messaging.hdr(data)
        msg = Messaging.MsgFactory(hdr)
        json = Messaging.toJson(msg)
        print(json)

class Control:
    def start(self):
        # general asyncio stuff
        asyncio.set_event_loop(loop)
        self.loop = asyncio.get_event_loop()

        # console input
        asyncio.ensure_future(handle_console_input())

        # tcp server
        self.tcp_server = self.loop.run_until_complete(asyncio.start_server(client_connected_handler, '127.0.0.1', 5678))
        
        # websocket server
        start_ws_server = websockets.serve(handle_ws_client, '127.0.0.1', 5679)
        self.loop.run_until_complete(start_ws_server)
        
        # kick things off
        self.loop.run_forever()
        self.stop()

    def stop(self):
        self.tcp_server.close()
        self.loop.stop()
        self.loop.close()

con = Control()
def background_thread_for_io():
    con.start()


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    #con.stop()
    con.tcp_server.close()
    con.loop.stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    thisFileDir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(thisFileDir+"/../MsgApp")
    from Messaging import Messaging
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/..")
    msgdir = srcroot+"/../obj/CodeGenerator/Python/"
    msgLib = Messaging(msgdir, 0, "NetworkHeader")

    from threading import Thread
    t = Thread(target=background_thread_for_io)
    t.start()

    _cmd = ""
    try:
        while True:
            cmd = input("")
            print("got input cmd " + cmd)
            msg = csvToMsg(cmd)
            if msg:
                msg_q.sync_q.put(msg)
    except SystemExit:
        print("exiting main")
