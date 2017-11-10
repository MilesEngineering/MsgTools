#!/usr/bin/env python3
import unittest
import sys
sys.path.append("..")
import ctypes

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
