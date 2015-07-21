#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append(".")
import MsgParser
sys.path.append("Cpp")
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
//  m/s
uint32_t GetFieldA()
{
    return Get_uint32_t(&m_data[0]);
}""")
        expected.append("""\
//  
uint32_t GetFABitsA()
{
    return (GetFieldA() >> 0) & 0x7fffffff;
}""")
        expected.append("""\
//  
uint16_t GetFieldB()
{
    return Get_uint16_t(&m_data[4]);
}""")
        expected.append("""\
//  
uint8_t GetFieldC(int idx)
{
    return Get_uint8_t(&m_data[6+idx*1]);
}""")
        expected.append("""\
//  
uint8_t GetFieldD()
{
    return Get_uint8_t(&m_data[11]);
}""")
        expected.append("""\
//  
float GetBitsA()
{
    return (float((GetFieldD() >> 0) & 0xf) / 14.357);
}""")
        expected.append("""\
//  
uint8_t GetBitsB()
{
    return (GetFieldD() >> 4) & 0x7;
}""")
        expected.append("""\
//  
uint8_t GetBitsC()
{
    return (GetFieldD() >> 7) & 0x1;
}""")
        expected.append("""\
//  
float GetFieldE()
{
    return Get_float(&m_data[12]);
}""")
        expected.append("""\
//  
float GetFieldF()
{
    return ((float(Get_uint16_t(&m_data[16])) / 2.7) + 1.828);
}""")
        expected.append("""\
//  m/s
void SetFieldA(uint32_t value)
{
    Set_uint32_t(&m_data[0], value);
}""")
        expected.append("""\
//  
void SetFABitsA(uint32_t value)
{
    SetFieldA((GetFieldA() & ~(0x7fffffff << 0)) | ((value & 0x7fffffff) << 0));
}""")
        expected.append("""\
//  
void SetFieldB(uint16_t value)
{
    Set_uint16_t(&m_data[4], value);
}""")
        expected.append("""\
//  
void SetFieldC(uint8_t value, int idx)
{
    Set_uint8_t(&m_data[6+idx*1], value);
}""")
        expected.append("""\
//  
void SetFieldD(uint8_t value)
{
    Set_uint8_t(&m_data[11], value);
}""")
        expected.append("""\
//  
void SetBitsA(float value)
{
    SetFieldD((GetFieldD() & ~(0xf << 0)) | ((uint8_t(value * 14.357) & 0xf) << 0));
}""")
        expected.append("""\
//  
void SetBitsB(uint8_t value)
{
    SetFieldD((GetFieldD() & ~(0x7 << 4)) | ((value & 0x7) << 4));
}""")
        expected.append("""\
//  
void SetBitsC(uint8_t value)
{
    SetFieldD((GetFieldD() & ~(0x1 << 7)) | ((value & 0x1) << 7));
}""")
        expected.append("""\
//  
void SetFieldE(float value)
{
    Set_float(&m_data[12], value);
}""")
        expected.append("""\
//  
void SetFieldF(float value)
{
    Set_uint16_t(&m_data[16], uint16_t((value - 1.828) * 2.7));
}""")
        expected.append("""\
//  
uint8_t* FieldC()
{
    return (uint8_t*)&m_data[6];
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
        expected = "MsgA"
        observed = MsgParser.msgName(MsgParser.Messages(self.msgDict)[0])
        self.assertMultiLineEqual(expected, observed)
        with self.assertRaises(IndexError):
            MsgParser.msgName(MsgParser.Messages(self.msgDict)[1])
    
    def test_enums(self):
        expected = 'enum EnumA {OptionA = 1, OptionB = 2, OptionC = 4, OptionD = 5};\n'
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
