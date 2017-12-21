#!/usr/bin/python

import bluetooth
import sys
DEVICE = 'c0:d3:c0:4a:dd:8e'
port = None

services = bluetooth.find_service(address=DEVICE)
for s in services:
    if s['name'] == 'AndroidServer':
        port = s['port']
if port == None:
    print "SDP says AndroidServer isn't present"
    sys.exit(0)
socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
socket.connect((DEVICE, port))
while True:
    print socket.recv(1024)
