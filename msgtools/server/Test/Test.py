#!/usr/bin/env python3
import unittest
import struct

from msgtools.lib.messaging import Messaging as M
from msgtools.lib.message import Message as Msg
from msgtools.server.CanPlugin import CanFragmentation

M.LoadAllMessages()

from msgtools.lib.messaging import Messaging

Messaging.debug = True

def test_msg_size(size):
    msg_in = M.Messages.BandwidthTest()
    msg_in.hdr.SetDataLength(size)
    msg_in.hdr.SetSource(11)
    msg_in.hdr.SetDestination(22)
    msg_in.hdr.SetPriority(1)
    for i in range(msg_in.GetTestData.count):
        msg_in.SetTestData(i,i)
    
    cf = CanFragmentation()
    cf.use_print = True
    can_packets = cf.fragment(msg_in.hdr)
    msgs_out = []
    for rx_frame in can_packets:
        hdr = cf.reassemble(rx_frame)
        if hdr:
            msgs_out.append(Messaging.MsgFactory(hdr))
    # commented out code to cause a failure, so we can spot-check that
    # failure detection works
    #msg_in.SetTestData(99,3)
    #msg_in.hdr.SetSource(99)
    return (msg_in, msgs_out[0])
    
class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print ("----------- Running setup")

    def test_can_fragmentation(self):
        sizes = [42, 100, 121, 1,62,63,64,65,66,200,124,123,122,121,120]
        for size in sizes:
            (input, output) = test_msg_size(size)
            match = True
            if input.hdr.GetDataLength() != output.hdr.GetDataLength():
                match = False
                print("DataLength mismatch")
            if input.hdr.GetSource()      != output.hdr.GetSource():
                match = False
                print("Source mismatch")
            if input.hdr.GetDestination() != output.hdr.GetDestination():
                match = False
                print("Destination mismatch")
            if input.hdr.GetPriority()    != output.hdr.GetPriority():
                match = False
                print("Priority mismatch")
            try:
                for i in range(input.GetTestData.count):
                    if input.GetTestData(i) != output.GetTestData(i):
                        match = False
            except struct.error:
                pass
            if not match:
                print("Failure at size message size %d" % size)
                print(input.hdr)
                print(output.hdr)
                print(input)
                print(output)
                self.assertEqual(0, 1)
            


def main(args=None):
    unittest.main()

# main starts here
if __name__ == '__main__':
    main()
