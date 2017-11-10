#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("..")
import MsgParser
sys.path.append("../Java")
import language

class TestJava(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        with open("messages/TestCase1.yaml", 'r') as inputFile:
            self.msgIDL = inputFile.read()
        self.msgDict = yaml.load(self.msgIDL)

    def test_accessors(self):
        expected = []
        expected.append("""\
//  m/s, (0 to 4294967295)
public long GetFieldA()
{
    return (long)Integer.toUnsignedLong(m_data.getInt(0));
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
    return (int)Short.toUnsignedInt(m_data.getShort(4));
}""")
        expected.append("""\
//  , (0 to 255)
public short GetFieldC(int idx)
{
    return (short)Byte.toUnsignedInt(m_data.get(6+idx*1));
}""")
        expected.append("""\
//  , (0 to 255)
public short GetFieldD()
{
    return (short)Byte.toUnsignedInt(m_data.get(11));
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
//  , (1.828 to 176946.328)
public float GetFieldF()
{
    return (((float)((int)Short.toUnsignedInt(m_data.getShort(16))) * 2.7f) + 1.828f);
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
    SetFieldD((short)((GetFieldD() & ~(0xf << 0)) | ((short(value / 14.357f) & 0xf) << 0)));
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
//  , (1.828 to 176946.328)
public void SetFieldF(float value)
{
    m_data.putShort(16, (short)int((value - 1.828f) / 2.7f));
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
    private final int id;
    EnumA(int id) { this.id = id; }
    static Map<Integer, EnumA> map = new HashMap<>();
    static {
        for (EnumA key : EnumA.values()) {
            map.put(key.id, key);
        }
    }
    public int intValue() { return id; }
    public static EnumA construct(int value) { return map.get(value); }
}
'''
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        expected = []
        expected.append("SetFieldA(1);")
        expected.append("SetFieldB(2);")
        expected.append("for (int i=0; i<5; i++)\n    SetFieldC(3, i);")
        expected.append("SetBitsA(7.1);")
        expected.append("SetBitsC(1);")
        expected.append("SetFieldE(3.14159);")
        expected.append("SetFieldF(3.14);")
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
