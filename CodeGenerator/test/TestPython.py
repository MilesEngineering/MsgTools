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
        with open("TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL)

    def test_accessors(self):
        expected = []
        expected.append("""\
@staticmethod
@msg.units('m/s')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('4294967295')
@msg.count(1)
def GetFieldA(message_buffer):
    \"\"\"\"\"\"
    value = struct.unpack_from('>L', message_buffer, MsgA.MSG_OFFSET + 0)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('2147483647')
@msg.count(1)
def GetFABitsA(message_buffer):
    \"\"\"\"\"\"
    value = (MsgA.GetFieldA(message_buffer) >> 0) & 0x7fffffff
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('2')
@msg.minVal('0')
@msg.maxVal('65535')
@msg.count(1)
def GetFieldB(message_buffer):
    \"\"\"\"\"\"
    value = struct.unpack_from('>H', message_buffer, MsgA.MSG_OFFSET + 4)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3')
@msg.minVal('0')
@msg.maxVal('255')
@msg.count(5)
def GetFieldC(message_buffer, idx):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', message_buffer, MsgA.MSG_OFFSET + 6+idx*1)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('255')
@msg.count(1)
def GetFieldD(message_buffer):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', message_buffer, MsgA.MSG_OFFSET + 11)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('7.1')
@msg.minVal('0.0')
@msg.maxVal('215.355')
@msg.count(1)
def GetBitsA(message_buffer):
    \"\"\"\"\"\"
    value = (float((MsgA.GetFieldD(message_buffer) >> 0) & 0xf) * 14.357)
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('7')
@msg.count(1)
def GetBitsB(message_buffer):
    \"\"\"\"\"\"
    value = (MsgA.GetFieldD(message_buffer) >> 4) & 0x7
    value = MsgA.ReverseEnumA.get(value, value)
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('1')
@msg.count(1)
def GetBitsC(message_buffer):
    \"\"\"\"\"\"
    value = (MsgA.GetFieldD(message_buffer) >> 7) & 0x1
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3.14159')
@msg.minVal('0.0')
@msg.maxVal('10.0')
@msg.count(1)
def GetFieldE(message_buffer):
    \"\"\"\"\"\"
    value = struct.unpack_from('>f', message_buffer, MsgA.MSG_OFFSET + 12)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.count(1)
def GetFieldF(message_buffer):
    \"\"\"\"\"\"
    value = struct.unpack_from('>H', message_buffer, MsgA.MSG_OFFSET + 16)[0]
    value = ((value * 2.7) + 1.828)
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('m/s')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('4294967295')
@msg.count(1)
def SetFieldA(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 4294967295)
    struct.pack_into('>L', message_buffer, MsgA.MSG_OFFSET + 0, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('2147483647')
@msg.count(1)
def SetFABitsA(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 2147483647)
    MsgA.SetFieldA(message_buffer, (MsgA.GetFieldA(message_buffer) & ~(0x7fffffff << 0)) | ((tmp & 0x7fffffff) << 0))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('2')
@msg.minVal('0')
@msg.maxVal('65535')
@msg.count(1)
def SetFieldB(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 65535)
    struct.pack_into('>H', message_buffer, MsgA.MSG_OFFSET + 4, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3')
@msg.minVal('0')
@msg.maxVal('255')
@msg.count(5)
def SetFieldC(message_buffer, value, idx):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 255)
    struct.pack_into('B', message_buffer, MsgA.MSG_OFFSET + 6+idx*1, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('255')
@msg.count(1)
def SetFieldD(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 255)
    struct.pack_into('B', message_buffer, MsgA.MSG_OFFSET + 11, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('7.1')
@msg.minVal('0.0')
@msg.maxVal('215.355')
@msg.count(1)
def SetBitsA(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(int(value / 14.357), 0), 15)
    MsgA.SetFieldD(message_buffer, (MsgA.GetFieldD(message_buffer) & ~(0xf << 0)) | ((tmp & 0xf) << 0))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('')
@msg.minVal('0')
@msg.maxVal('7')
@msg.count(1)
def SetBitsB(message_buffer, value):
    \"\"\"\"\"\"
    defaultValue = 0
    try:
        value = int(float(value))
    except ValueError:
        pass
    if isinstance(value, int) or value.isdigit():
        defaultValue = int(value)
    value = MsgA.EnumA.get(value, defaultValue)
    tmp = min(max(value, 0), 7)
    MsgA.SetFieldD(message_buffer, (MsgA.GetFieldD(message_buffer) & ~(0x7 << 4)) | ((tmp & 0x7) << 4))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('1')
@msg.minVal('0')
@msg.maxVal('1')
@msg.count(1)
def SetBitsC(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(value, 0), 1)
    MsgA.SetFieldD(message_buffer, (MsgA.GetFieldD(message_buffer) & ~(0x1 << 7)) | ((tmp & 0x1) << 7))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3.14159')
@msg.minVal('0.0')
@msg.maxVal('10.0')
@msg.count(1)
def SetFieldE(message_buffer, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('>f', message_buffer, MsgA.MSG_OFFSET + 12, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.default('3.14')
@msg.minVal('1.828')
@msg.maxVal('176946.328')
@msg.count(1)
def SetFieldF(message_buffer, value):
    \"\"\"\"\"\"
    tmp = min(max(int((value - 1.828) / 2.7), 0), 65535)
    struct.pack_into('>H', message_buffer, MsgA.MSG_OFFSET + 16, tmp)
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
        expected = "MsgA"
        observed = MsgParser.msgName(MsgParser.Messages(self.msgDict)[0])
        self.assertMultiLineEqual(expected, observed)
        with self.assertRaises(IndexError):
            MsgParser.msgName(MsgParser.Messages(self.msgDict)[1])
    
    def test_enums(self):
        expected = 'EnumA = {"OptionA" : 1, "OptionB" : 2, "OptionC" : 4, "OptionD" : 5}\nReverseEnumA = {1 : "OptionA", 2 : "OptionB", 4 : "OptionC", 5 : "OptionD"}\n'
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        messageName = MsgParser.Messages(self.msgDict)[0]["Name"]

        expected = []
        expected.append(messageName + ".SetFieldA(message_buffer, 1)")
        expected.append(messageName + ".SetFieldB(message_buffer, 2)")
        expected.append("for i in range(0,5):")
        expected.append("    "+messageName + ".SetFieldC(message_buffer, 3, i)")
        expected.append(messageName + ".SetBitsA(message_buffer, 7.1)")
        expected.append(messageName + ".SetBitsC(message_buffer, 1)")
        expected.append(messageName + ".SetFieldE(message_buffer, 3.14159)")
        expected.append(messageName + ".SetFieldF(message_buffer, 3.14)")

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
