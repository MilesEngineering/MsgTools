#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("../../..")
import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import PatchStructs
sys.path.append("../python")
import language

class TestCpp(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with open("messages/TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL, Loader=yaml.SafeLoader)
        PatchStructs(self.msgDict)

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
    value = struct.unpack_from('<L', self.rawBuffer(), TestCase1.MSG_OFFSET + 0)[0]
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
    value = struct.unpack_from('<H', self.rawBuffer(), TestCase1.MSG_OFFSET + 4)[0]
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
def GetBitsA(self, convertFloat=True):
    \"\"\"\"\"\"
    value = (self.GetFieldD() >> 0) & 0xf
    if convertFloat:
        value = (float(value) * 14.357)
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
def GetBitsB(self, enumAsInt=False):
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
    value = struct.unpack_from('<f', self.rawBuffer(), TestCase1.MSG_OFFSET + 12)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('-2147483648')
@msg.maxVal('2147483647')
@msg.offset('16')
@msg.size('4')
@msg.count(1)
def GetFieldS1_Member1(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('<l', self.rawBuffer(), TestCase1.MSG_OFFSET + 16)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('DBL_MIN')
@msg.maxVal('DBL_MAX')
@msg.offset('20')
@msg.size('8')
@msg.count(1)
def GetFieldS1_Member2(self):
    \"\"\"\"\"\"
    value = struct.unpack_from('<d', self.rawBuffer(), TestCase1.MSG_OFFSET + 20)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.offset('28')
@msg.size('2')
@msg.count(1)
def GetFieldF(self, convertFloat=True):
    \"\"\"\"\"\"
    value = struct.unpack_from('<H', self.rawBuffer(), TestCase1.MSG_OFFSET + 28)[0]
    if convertFloat:
        value = ((value * 2.7) + 1.828)
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('-2147483648')
@msg.maxVal('2147483647')
@msg.offset('30')
@msg.size('4')
@msg.count(3)
def GetFieldS2_Member1(self, idx):
    \"\"\"\"\"\"
    value = struct.unpack_from('<l', self.rawBuffer(), TestCase1.MSG_OFFSET + 30+idx*12)[0]
    return value
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('DBL_MIN')
@msg.maxVal('DBL_MAX')
@msg.offset('34')
@msg.size('8')
@msg.count(3)
def GetFieldS2_Member2(self, idx):
    \"\"\"\"\"\"
    value = struct.unpack_from('<d', self.rawBuffer(), TestCase1.MSG_OFFSET + 34+idx*12)[0]
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
    value = min(max(value, 0), 4294967295)
    struct.pack_into('<L', self.rawBuffer(), TestCase1.MSG_OFFSET + 0, value)
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
    value = min(max(value, 0), 2147483647)
    self.SetFieldA((self.GetFieldA() & ~(0x7fffffff << 0)) | ((value & 0x7fffffff) << 0))
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
    value = min(max(value, 0), 65535)
    struct.pack_into('<H', self.rawBuffer(), TestCase1.MSG_OFFSET + 4, value)
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
    value = min(max(value, 0), 255)
    struct.pack_into('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 6+idx*1, value)
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
    value = min(max(value, 0), 255)
    struct.pack_into('B', self.rawBuffer(), TestCase1.MSG_OFFSET + 11, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('7.1')
@msg.minVal('0.0')
@msg.maxVal('215.355')
@msg.offset('11')
@msg.size('0')
@msg.count(1)
def SetBitsA(self, value, convertFloat=True):
    \"\"\"\"\"\"
    if convertFloat:
        value = int(value / 14.357)
    value = min(max(value, 0), 15)
    self.SetFieldD((self.GetFieldD() & ~(0xf << 0)) | ((value & 0xf) << 0))
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
    value = min(max(value, 0), 7)
    self.SetFieldD((self.GetFieldD() & ~(0x7 << 4)) | ((value & 0x7) << 4))
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
    value = min(max(value, 0), 1)
    self.SetFieldD((self.GetFieldD() & ~(0x1 << 7)) | ((value & 0x1) << 7))
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
    struct.pack_into('<f', self.rawBuffer(), TestCase1.MSG_OFFSET + 12, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('-2147483648')
@msg.maxVal('2147483647')
@msg.offset('16')
@msg.size('4')
@msg.count(1)
def SetFieldS1_Member1(self, value):
    \"\"\"\"\"\"
    value = min(max(value, -2147483648), 2147483647)
    struct.pack_into('<l', self.rawBuffer(), TestCase1.MSG_OFFSET + 16, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('DBL_MIN')
@msg.maxVal('DBL_MAX')
@msg.offset('20')
@msg.size('8')
@msg.count(1)
def SetFieldS1_Member2(self, value):
    \"\"\"\"\"\"
    struct.pack_into('<d', self.rawBuffer(), TestCase1.MSG_OFFSET + 20, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.offset('28')
@msg.size('2')
@msg.count(1)
def SetFieldF(self, value, convertFloat=True):
    \"\"\"\"\"\"
    if convertFloat:
        value = int((value - 1.828) / 2.7)
    value = min(max(value, 0), 65535)
    struct.pack_into('<H', self.rawBuffer(), TestCase1.MSG_OFFSET + 28, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('-2147483648')
@msg.maxVal('2147483647')
@msg.offset('30')
@msg.size('4')
@msg.count(3)
def SetFieldS2_Member1(self, value, idx):
    \"\"\"\"\"\"
    value = min(max(value, -2147483648), 2147483647)
    struct.pack_into('<l', self.rawBuffer(), TestCase1.MSG_OFFSET + 30+idx*12, value)
""")
        expected.append("""\
@msg.units('')
@msg.default('')
@msg.minVal('DBL_MIN')
@msg.maxVal('DBL_MAX')
@msg.offset('34')
@msg.size('8')
@msg.count(3)
def SetFieldS2_Member2(self, value, idx):
    \"\"\"\"\"\"
    struct.pack_into('<d', self.rawBuffer(), TestCase1.MSG_OFFSET + 34+idx*12, value)
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

def main(args=None):
    unittest.main()

# main starts here
if __name__ == '__main__':
    main()
