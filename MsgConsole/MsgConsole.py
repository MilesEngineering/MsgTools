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

async def handle_tcp_client(client_reader):
    #print("handle_tcp_client")
    while True:
        # we *should* read Messaging.hdr.SIZE bytes,
        # then parse header to see body length,
        # then read those bytes.
        data = await client_reader.read(1024)
        if not data:
            break
        await consoleserver.send_to_others(client_reader, data)

def client_connected_handler(client_reader, client_writer):
    # Start a new asyncio.Task to handle this specific client connection
    task = asyncio.Task(handle_tcp_client(client_reader))
    print("Added new client to list of " + str(len(consoleserver.tcp_clients)) + " clients")
    consoleserver.tcp_clients[task] = (client_reader, client_writer)

    def client_done(task):
        print("client exited")
        # When the tasks that handles the specific client connection is done
        del consoleserver.tcp_clients[task]

    # Add the client_done callback to be run when the future becomes done
    task.add_done_callback(client_done)

async def handle_console_input():
    loop = asyncio.get_event_loop()
    while True:
        data = await consoleserver.msg_q.async_q.get()
        await consoleserver.send_to_others(consoleserver.msg_q, data)

async def handle_ws_client(websocket, path):
    consoleserver.ws_clients[websocket] = websocket
    print("websocket connected")
    try:
        while True:
            data = await websocket.recv()
            if not data:
                break
            await consoleserver.send_to_others(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        print("websocket closed")
        del consoleserver.ws_clients[websocket]

class ConsoleServer:
    def start(self):
        # general asyncio stuff
        asyncio.set_event_loop(loop)
        self.loop = asyncio.get_event_loop()

        # console input
        self.msg_q = janus.Queue(loop=loop)
        asyncio.ensure_future(handle_console_input())

        # client lists
        self.tcp_clients = {} # task -> (reader, writer)
        self.ws_clients = {}

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
    
    async def send_to_others(self, me, data):
        if me != self.msg_q:
            try:
                # print as JSON for debug purposes
                hdr = Messaging.hdr(data)
                msg = Messaging.MsgFactory(hdr)
                json = Messaging.toJson(msg)
                print(json)
            except:
                pass

        #for connection in connections.keys():
        #    if connection != me:
        #        connection.sendMsg(msg)

        # send to Websocket clients
        for ws in consoleserver.ws_clients.keys():
            if ws != me:
                # calling ws.send REQUIRES an 'await', otherwise data never gets to the ws client!
                await ws.send(data)

        # send to TCP clients
        for task in consoleserver.tcp_clients.keys():
                (reader, writer) = consoleserver.tcp_clients[task]
                if reader != me:
                    writer.write(data)

consoleserver = ConsoleServer()

def background_thread_for_io():
    consoleserver.start()

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    #consoleserver.stop()
    consoleserver.tcp_server.close()
    consoleserver.loop.stop()
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
            #print("got input cmd [" + cmd + "]")
            if cmd:
                msg = Messaging.csvToMsg(cmd)
                if msg:
                    consoleserver.msg_q.sync_q.put(msg.rawBuffer().raw)
    except SystemExit:
        print("exiting main")
