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

if __name__ == '__main__':
    unittest.main()
