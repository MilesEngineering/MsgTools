#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("..")
import MsgParser
sys.path.append("../Python")
import language

class TestCpp(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with open("messages/TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL)

    def test_accessors(self):
        expected = []
        expected.append("""\
@msg.units('m/s')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('4294967295')
@msg.offset('0')
@msg.size('4')
@msg.count(1)
def GetFieldA(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('>L', self.rawBuffer(), TestCase1.MSG_OFFSET + 0)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('2147483647')
@msg.offset('0')
@msg.size('0')
@msg.count(1)
def GetFABitsA(self):
    \"\"\"\"\"\"
    value = (self.GetFieldA() >> 0) & 0x7fffffff
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('2')
@msg.minVal('0')
@msg.maxVal('65535')
@msg.offset('4')
@msg.size('2')
@msg.count(1)
def GetFieldB(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('>H', self.rawBuffer(), TestCase1.MSG_OFFSET + 4)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('3')
@msg.minVal('0')
@msg.maxVal('255')
@msg.offset('6')
@msg.size('1')
@msg.count(5)
def GetFieldC(self, idx):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 6+idx*1)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('255')
@msg.offset('11')
@msg.size('1')
@msg.count(1)
def GetFieldD(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 11)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('7.1')
@msg.minVal('0.0')
@msg.maxVal('215.355')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def GetBitsA(self):
    \"\"\"\"\"\"
    value = (float((self.GetFieldD() >> 0) & 0xf) * 14.357)
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('7')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def GetBitsB(self, enumAsInt=0):
    \"\"\"\"\"\"
    value = (self.GetFieldD() >> 4) & 0x7
    if not enumAsInt:
        value = TestCase1.ReverseEnumA.get(value, value)
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('1')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def GetBitsC(self):
    \"\"\"\"\"\"
    value = (self.GetFieldD() >> 7) & 0x1
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14159')
@msg.minVal('0.0')
@msg.maxVal('10.0')
@msg.offset('12')
@msg.size('4')
@msg.count(1)
def GetFieldE(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('>f', self.rawBuffer(), TestCase1.MSG_OFFSET + 12)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.offset('16')
@msg.size('2')
@msg.count(1)
def GetFieldF(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('>H', self.rawBuffer(), TestCase1.MSG_OFFSET + 16)[0]
    value = ((value * 2.7) + 1.828)
    return value
""")
        expected.append("""\
@msg.units('m/s')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('4294967295')
@msg.offset('0')
@msg.size('4')
@msg.count(1)
def SetFieldA(self, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 4294967295)
    struct.pack_into('>L', self.rawBuffer(), TestCase1.MSG_OFFSET + 0, tmp)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('2147483647')
@msg.offset('0')
@msg.size('0')
@msg.count(1)
def SetFABitsA(self, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 2147483647)
    self.SetFieldA((self.GetFieldA() & ~(0x7fffffff << 0)) | ((tmp & 0x7fffffff) << 0))
""")
        expected.append("""\
@msg.units('')
@msg.default('2')
@msg.minVal('0')
@msg.maxVal('65535')
@msg.offset('4')
@msg.size('2')
@msg.count(1)
def SetFieldB(self, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 65535)
    struct.pack_into('>H', self.rawBuffer(), TestCase1.MSG_OFFSET + 4, tmp)
""")
        expected.append("""\
@msg.units('')
@msg.default('3')
@msg.minVal('0')
@msg.maxVal('255')
@msg.offset('6')
@msg.size('1')
@msg.count(5)
def SetFieldC(self, value, idx):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 255)
    struct.pack_into('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 6+idx*1, tmp)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('255')
@msg.offset('11')
@msg.size('1')
@msg.count(1)
def SetFieldD(self, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 255)
    struct.pack_into('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 11, tmp)
""")
        expected.append("""\
@msg.units('')
@msg.default('7.1')
@msg.minVal('0.0')
@msg.maxVal('215.355')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def SetBitsA(self, value):
    \"\"\"\"\"\"
    tmp = min(max(int(value / 14.357), 0), 15)
    self.SetFieldD((self.GetFieldD() & ~(0xf << 0)) | ((tmp & 0xf) << 0))
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('7')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def SetBitsB(self, value):
    \"\"\"\"\"\"
    defaultValue = 0
    try:
        value = int(float(value))
    except ValueError:
        pass
    if isinstance(value, int) or value.isdigit():
        defaultValue = int(value)
    value = TestCase1.EnumA.get(value, defaultValue)
    tmp = min(max(value, 0), 7)
    self.SetFieldD((self.GetFieldD() & ~(0x7 << 4)) | ((tmp & 0x7) << 4))
""")
        expected.append("""\
@msg.units('')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('1')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def SetBitsC(self, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 1)
    self.SetFieldD((self.GetFieldD() & ~(0x1 << 7)) | ((tmp & 0x1) << 7))
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14159')
@msg.minVal('0.0')
@msg.maxVal('10.0')
@msg.offset('12')
@msg.size('4')
@msg.count(1)
def SetFieldE(self, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('>f', self.rawBuffer(), TestCase1.MSG_OFFSET + 12, tmp)
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.offset('16')
@msg.size('2')
@msg.count(1)
def SetFieldF(self, value):
    \"\"\"\"\"\"
    tmp = min(max(int((value - 1.828) / 2.7), 0), 65535)
    struct.pack_into('>H', self.rawBuffer(), TestCase1.MSG_OFFSET + 16, tmp)
""")
        expCount = len(expected)
        observed = language.accessors(MsgParser.Messages(self.msgDict)[0])
        obsCount = len(observed)
        self.assertEqual(expCount, obsCount)
        
        for i in range(expCount):
            self.assertMultiLineEqual(expected[i], observed[i])
        with self.assertRaises(IndexError):
            language.accessors(MsgParser.Messages(self.msgDict)[1])

    def test_msgNames(self):
        expected = "TestCase1"
        observed = MsgParser.msgName(MsgParser.Messages(self.msgDict)[0])
        self.assertMultiLineEqual(expected, observed)
        with self.assertRaises(IndexError):
            MsgParser.msgName(MsgParser.Messages(self.msgDict)[1])
    
    def test_enums(self):
        expected = 'EnumA = OrderedDict([("OptionA", 1), ("OptionB", 2), ("OptionC", 4), ("OptionD", 5)])\nReverseEnumA = OrderedDict([(1, "OptionA"), (2, "OptionB"), (4, "OptionC"), (5, "OptionD")])\n'
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        expected = []
        expected.append("self.SetFieldA(1)")
        expected.append("self.SetFieldB(2)")
        expected.append("for i in range(0,5):")
        expected.append("    "+"self.SetFieldC(3, i)")
        expected.append("self.SetBitsA(7.1)")
        expected.append("self.SetBitsC(1)")
        expected.append("self.SetFieldE(3.14159)")
        expected.append("self.SetFieldF(3.14)")

        expCount = len(expected)

        observed = language.initCode(MsgParser.Messages(self.msgDict)[0])
        
        obsCount = len(observed)
        
        self.assertEqual(expCount, obsCount)

        for i in range(expCount):
            self.assertMultiLineEqual(expected[i], observed[i])

        with self.assertRaises(IndexError):
            language.initCode(MsgParser.Messages(self.msgDict)[1])

if __name__ == '__main__':
    unittest.main()
