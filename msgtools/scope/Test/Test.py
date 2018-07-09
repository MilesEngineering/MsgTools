#!/usr/bin/env python3
import unittest
import sys
import ctypes

try:
    from msgtools.lib.messaging import Messaging
except ImportError:
    import os
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.append(srcroot)
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
