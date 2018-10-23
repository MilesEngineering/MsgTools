#!/usr/bin/env python3
import os
import unittest
import sys
import ctypes

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../../..")
    sys.path.insert(1, srcroot)
from msgtools.lib.messaging import Messaging

class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print ("----------- Running setup")

    def test_example(self):
        self.assertEqual(1, 1)

def main(args=None):
    unittest.main()

# main starts here
if __name__ == '__main__':
    main()
