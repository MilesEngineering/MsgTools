import unittest
import yaml
import sys
sys.path.append(".")
import MsgParser
sys.path.append("Python")
import language

class TestCpp(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with open("test/TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL)

    def test_accessors(self):
        expected = []
        expected.append("""\
@staticmethod
@msg.units('m/s')
@msg.defaultValue('')
@msg.count(1)
def GetFieldA(bytes):
    \"\"\"\"\"\"
    value = struct.unpack_from('>L', bytes, 0)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldABitsA(bytes):
    \"\"\"\"\"\"
    return (GetFieldA(bytes) >> 0) & 0x7fffffff
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldB(bytes):
    \"\"\"\"\"\"
    value = struct.unpack_from('>H', bytes, 4)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(5)
def GetFieldC(bytes, idx):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', bytes, 6+idx*1)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldD(bytes):
    \"\"\"\"\"\"
    value = struct.unpack_from('B', bytes, 11)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldDBitsA(bytes):
    \"\"\"\"\"\"
    return (GetFieldD(bytes) >> 0) & 0xf
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldDBitsB(bytes):
    \"\"\"\"\"\"
    return (GetFieldD(bytes) >> 4) & 0x7
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldDBitsC(bytes):
    \"\"\"\"\"\"
    return (GetFieldD(bytes) >> 7) & 0x1
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def GetFieldE(bytes):
    \"\"\"\"\"\"
    value = struct.unpack_from('>f', bytes, 12)[0]
    return value
""")
        expected.append("""\
@staticmethod
@msg.units('m/s')
@msg.defaultValue('')
@msg.count(1)
def SetFieldA(bytes, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('>L', bytes, 0, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldABitsA(bytes, value):
    \"\"\"\"\"\"
    SetFieldA(bytes, (GetFieldA(bytes) & ~(0x7fffffff << 0)) | ((value & 0x7fffffff) << 0))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldB(bytes, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('>H', bytes, 4, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(5)
def SetFieldC(bytes, value, idx):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('B', bytes, 6+idx*1, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldD(bytes, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('B', bytes, 11, tmp)
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldDBitsA(bytes, value):
    \"\"\"\"\"\"
    SetFieldD(bytes, (GetFieldD(bytes) & ~(0xf << 0)) | ((value & 0xf) << 0))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldDBitsB(bytes, value):
    \"\"\"\"\"\"
    SetFieldD(bytes, (GetFieldD(bytes) & ~(0x7 << 4)) | ((value & 0x7) << 4))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldDBitsC(bytes, value):
    \"\"\"\"\"\"
    SetFieldD(bytes, (GetFieldD(bytes) & ~(0x1 << 7)) | ((value & 0x1) << 7))
""")
        expected.append("""\
@staticmethod
@msg.units('')
@msg.defaultValue('')
@msg.count(1)
def SetFieldE(bytes, value):
    \"\"\"\"\"\"
    tmp = value
    struct.pack_into('>f', bytes, 12, tmp)
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
        expected = 'EnumA = {"OptionA" : 1, "OptionB" : 2, "OptionC" : 4, "OptionD" : 5}\n'
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        expected = []
        expected.append("SetFieldA(1)")
        expected.append("SetFieldB(2)")
        expected.append("SetFieldC(3)")
        expected.append("SetFieldDBitsA(7)")
        expected.append("SetFieldDBitsC(1)")
        expected.append("SetFieldE(3.14159)")
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
