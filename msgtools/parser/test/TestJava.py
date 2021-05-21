#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("../../..")
import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import PatchStructs
sys.path.append("../java")
import language

class TestJava(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with open("messages/TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL, Loader=yaml.SafeLoader)
        PatchStructs(self.msgDict)

    def test_accessors(self):
        expected = []
        expected.append("""\
//  m/s, (0 to 4294967295)
public long GetFieldA()
{
    return (long)FieldAccess.toUnsignedLong(m_data.getInt(0));
}""")
        expected.append("""\
//  , (0 to 2147483647)
public long GetFABitsA()
{
    return (long)((GetFieldA() >> 0) & 0x7fffffff);
}""")
        expected.append("""\
//  , (0 to 65535)
public int GetFieldB()
{
    return (int)FieldAccess.toUnsignedInt(m_data.getShort(4));
}""")
        expected.append("""\
//  , (0 to 255)
public short GetFieldC(int idx)
{
    return (short)FieldAccess.toUnsignedInt(m_data.get(6+idx*1));
}""")
        expected.append("""\
//  , (0 to 255)
public short GetFieldD()
{
    return (short)FieldAccess.toUnsignedInt(m_data.get(11));
}""")
        expected.append("""\
//  , (0.0 to 215.355)
public float GetBitsA()
{
    return ((float)((GetFieldD() >> 0) & 0xf) * 14.357f);
}""")
        expected.append("""\
//  , (0 to 7)
public short GetBitsB()
{
    return (short)((GetFieldD() >> 4) & 0x7);
}""")
        expected.append("""\
//  , (0 to 1)
public short GetBitsC()
{
    return (short)((GetFieldD() >> 7) & 0x1);
}""")
        expected.append("""\
//  , (0.0 to 10.0)
public float GetFieldE()
{
    return (float)m_data.getFloat(12);
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
public int GetFieldS1_Member1()
{
    return (int)m_data.getInt(16);
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
public double GetFieldS1_Member2()
{
    return (double)m_data.getDouble(20);
}""")
        expected.append("""\
//  , (1.828 to 176946.328)
public float GetFieldF()
{
    return (((float)((int)FieldAccess.toUnsignedInt(m_data.getShort(28))) * 2.7f) + 1.828f);
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
public int GetFieldS2_Member1(int idx)
{
    return (int)m_data.getInt(30+idx*12);
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
public double GetFieldS2_Member2(int idx)
{
    return (double)m_data.getDouble(34+idx*12);
}""")
        expected.append("""\
//  m/s, (0 to 4294967295)
public void SetFieldA(long value)
{
    m_data.putInt(0, (int)value);
}""")
        expected.append("""\
//  , (0 to 2147483647)
public void SetFABitsA(long value)
{
    SetFieldA((long)((GetFieldA() & ~(0x7fffffff << 0)) | ((value & 0x7fffffff) << 0)));
}""")
        expected.append("""\
//  , (0 to 65535)
public void SetFieldB(int value)
{
    m_data.putShort(4, (short)value);
}""")
        expected.append("""\
//  , (0 to 255)
public void SetFieldC(short value, int idx)
{
    m_data.put(6+idx*1, (byte)value);
}""")
        expected.append("""\
//  , (0 to 255)
public void SetFieldD(short value)
{
    m_data.put(11, (byte)value);
}""")
        expected.append("""\
//  , (0.0 to 215.355)
public void SetBitsA(float value)
{
    SetFieldD((short)((GetFieldD() & ~(0xf << 0)) | (((short)(value / 14.357f) & 0xf) << 0)));
}""")
        expected.append("""\
//  , (0 to 7)
public void SetBitsB(short value)
{
    SetFieldD((short)((GetFieldD() & ~(0x7 << 4)) | ((value & 0x7) << 4)));
}""")
        expected.append("""\
//  , (0 to 1)
public void SetBitsC(short value)
{
    SetFieldD((short)((GetFieldD() & ~(0x1 << 7)) | ((value & 0x1) << 7)));
}""")
        expected.append("""\
//  , (0.0 to 10.0)
public void SetFieldE(float value)
{
    m_data.putFloat(12, (float)value);
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
public void SetFieldS1_Member1(int value)
{
    m_data.putInt(16, (int)value);
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
public void SetFieldS1_Member2(double value)
{
    m_data.putDouble(20, (double)value);
}""")
        expected.append("""\
//  , (1.828 to 176946.328)
public void SetFieldF(float value)
{
    m_data.putShort(28, (short)(int)((value - 1.828f) / 2.7f));
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
public void SetFieldS2_Member1(int value, int idx)
{
    m_data.putInt(30+idx*12, (int)value);
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
public void SetFieldS2_Member2(double value, int idx)
{
    m_data.putDouble(34+idx*12, (double)value);
}""")
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
        expected = '''public enum EnumA {
    OptionA(1), OptionB(2), OptionC(4), OptionD(5);
    private final long id;
    EnumA(long id) { this.id = id; }
    static Map<Long, EnumA> map = new HashMap<>();
    static {
        for (EnumA key : EnumA.values()) {
            map.put(key.id, key);
        }
    }
    public long intValue() { return id; }
    public static EnumA construct(long value) { return map.get(value); }
}
'''
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        expected = []
        expected.append("SetFieldA((long)1);")
        expected.append("SetFieldB((int)2);")
        expected.append("for (int i=0; i<5; i++)\n    SetFieldC((short)3, i);")
        expected.append("SetBitsA((short)7.1);")
        expected.append("SetBitsC((short)1);")
        expected.append("SetFieldE((float)3.14159);")
        expected.append("SetFieldF((int)3.14);")
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
