
#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("../../..")
import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import PatchStructs
sys.path.append("../cpp")
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
/*  m/s, (0 to 4294967295)*/
uint32_t GetFieldA() const
{
    return GetAlignedLE_uint32_t(&m_data[0]);
}""")
        expected.append("""\
/*  , (0 to 2147483647)*/
uint32_t GetFABitsA() const
{
    return (GetFieldA() >> 0) & 0x7fffffff;
}""")
        expected.append("""\
/*  , (0 to 65535)*/
uint16_t GetFieldB() const
{
    return GetAlignedLE_uint16_t(&m_data[4]);
}""")
        expected.append("""\
/*  , (0 to 255)*/
uint8_t GetFieldC(int idx) const
{
    return GetAlignedLE_uint8_t(&m_data[6+idx*1]);
}""")
        expected.append("""\
/*  , (0 to 255)*/
uint8_t GetFieldD() const
{
    return GetAlignedLE_uint8_t(&m_data[11]);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (0.0 to 215.355)*/
float GetBitsA() const
{
    return (float((GetFieldD() >> 0) & 0xf) * 14.357f);
}
#endif
""")
        expected.append("""\
/*  , (0.0 to 215.355)*/
uint8_t GetBitsAAsInt() const
{
    return (GetFieldD() >> 0) & 0xf;
}""")
        expected.append("""\
/*  , (0 to 7)*/
EnumA GetBitsB() const
{
    return EnumA((GetFieldD() >> 4) & 0x7);
}""")
        expected.append("""\
/*  , (0 to 1)*/
uint8_t GetBitsC() const
{
    return (GetFieldD() >> 7) & 0x1;
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (0.0 to 10.0)*/
float GetFieldE() const
{
    return GetAlignedLE_float(&m_data[12]);
}
#endif
""")
        expected.append("""\
/*  , (-2147483648 to 2147483647)*/
int32_t GetFieldS1_Member1() const
{
    return GetAlignedLE_int32_t(&m_data[16]);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (DBL_MIN to DBL_MAX)*/
double GetFieldS1_Member2() const
{
    return GetLE_double(&m_data[20]);
}
#endif
""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (1.828 to 176946.328)*/
float GetFieldF() const
{
    return ((float(GetAlignedLE_uint16_t(&m_data[28])) * 2.7f) + 1.828f);
}
#endif
""")
        expected.append("""\
/*  , (1.828 to 176946.328)*/
uint16_t GetFieldFAsInt() const
{
    return GetAlignedLE_uint16_t(&m_data[28]);
}""")
        expected.append("""\
/*  , (-2147483648 to 2147483647)*/
int32_t GetFieldS2_Member1(int idx) const
{
    return GetLE_int32_t(&m_data[30+idx*12]);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (DBL_MIN to DBL_MAX)*/
double GetFieldS2_Member2(int idx) const
{
    return GetLE_double(&m_data[34+idx*12]);
}
#endif
""")
        expected.append("""\
/* Test Field G, array of bitfields , (0 to 65535)*/
uint16_t GetFieldG(int idx) const
{
    return GetAlignedLE_uint16_t(&m_data[66+idx*2]);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  m/s, (0.0 to 215.355)*/
float GetBitsD(int idx) const
{
    return (float((GetFieldG(idx) >> 0) & 0xf) * 14.357f);
}
#endif
""")
        expected.append("""\
/*  m/s, (0.0 to 215.355)*/
uint16_t GetBitsDAsInt(int idx) const
{
    return (GetFieldG(idx) >> 0) & 0xf;
}""")
        expected.append("""\
/*  m/s2, (0 to 511)*/
uint16_t GetBitsE(int idx) const
{
    return (GetFieldG(idx) >> 4) & 0x1ff;
}""")
        expected.append("""\
/*  m/s, (0 to 4294967295)*/
void SetFieldA(uint32_t value)
{
    SetAlignedLE_uint32_t(&m_data[0], value);
}""")
        expected.append("""\
/*  , (0 to 2147483647)*/
void SetFABitsA(uint32_t value)
{
    SetFieldA((GetFieldA() & ~(0x7fffffff << 0)) | ((value & 0x7fffffff) << 0));
}""")
        expected.append("""\
/*  , (0 to 65535)*/
void SetFieldB(uint16_t value)
{
    SetAlignedLE_uint16_t(&m_data[4], value);
}""")
        expected.append("""\
/*  , (0 to 255)*/
void SetFieldC(uint8_t value, int idx)
{
    SetAlignedLE_uint8_t(&m_data[6+idx*1], value);
}""")
        expected.append("""\
/*  , (0 to 255)*/
void SetFieldD(uint8_t value)
{
    SetAlignedLE_uint8_t(&m_data[11], value);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (0.0 to 215.355)*/
void SetBitsA(float value)
{
    SetFieldD((GetFieldD() & ~(0xf << 0)) | (((uint8_t)(value / 14.357f) & 0xf) << 0));
}
#endif
""")
        expected.append("""\
/*  , (0.0 to 215.355)*/
void SetBitsAAsInt(uint8_t value)
{
    SetFieldD((GetFieldD() & ~(0xf << 0)) | ((value & 0xf) << 0));
}""")
        expected.append("""\
/*  , (0 to 7)*/
void SetBitsB(EnumA value)
{
    SetFieldD((GetFieldD() & ~(0x7 << 4)) | (((uint8_t)(value) & 0x7) << 4));
}""")
        expected.append("""\
/*  , (0 to 1)*/
void SetBitsC(uint8_t value)
{
    SetFieldD((GetFieldD() & ~(0x1 << 7)) | ((value & 0x1) << 7));
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (0.0 to 10.0)*/
void SetFieldE(float value)
{
    SetAlignedLE_float(&m_data[12], value);
}
#endif
""")
        expected.append("""\
/*  , (-2147483648 to 2147483647)*/
void SetFieldS1_Member1(int32_t value)
{
    SetAlignedLE_int32_t(&m_data[16], value);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (DBL_MIN to DBL_MAX)*/
void SetFieldS1_Member2(double value)
{
    SetLE_double(&m_data[20], value);
}
#endif
""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (1.828 to 176946.328)*/
void SetFieldF(float value)
{
    SetAlignedLE_uint16_t(&m_data[28], (uint16_t)((value - 1.828f) / 2.7f));
}
#endif
""")
        expected.append("""\
/*  , (1.828 to 176946.328)*/
void SetFieldFAsInt(uint16_t value)
{
    SetAlignedLE_uint16_t(&m_data[28], value);
}""")
        expected.append("""\
/*  , (-2147483648 to 2147483647)*/
void SetFieldS2_Member1(int32_t value, int idx)
{
    SetLE_int32_t(&m_data[30+idx*12], value);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  , (DBL_MIN to DBL_MAX)*/
void SetFieldS2_Member2(double value, int idx)
{
    SetLE_double(&m_data[34+idx*12], value);
}
#endif
""")
        expected.append("""\
/* Test Field G, array of bitfields , (0 to 65535)*/
void SetFieldG(uint16_t value, int idx)
{
    SetAlignedLE_uint16_t(&m_data[66+idx*2], value);
}""")
        expected.append("""\
#ifndef DISABLE_FLOAT_ACCESSORS
/*  m/s, (0.0 to 215.355)*/
void SetBitsD(float value, int idx)
{
    SetFieldG((GetFieldG(idx) & ~(0xf << 0)) | (((uint16_t)(value / 14.357f) & 0xf) << 0), idx);
}
#endif
""")
        expected.append("""\
/*  m/s, (0.0 to 215.355)*/
void SetBitsDAsInt(uint16_t value, int idx)
{
    SetFieldG((GetFieldG(idx) & ~(0xf << 0)) | ((value & 0xf) << 0), idx);
}""")
        expected.append("""\
/*  m/s2, (0 to 511)*/
void SetBitsE(uint16_t value, int idx)
{
    SetFieldG((GetFieldG(idx) & ~(0x1ff << 4)) | ((value & 0x1ff) << 4), idx);
}""")
        expected.append("""\
/*  , (0 to 255)*/
void CopyInFieldC(const uint8_t* in, int len)
{
    int count = ((len < 5) ? len : 5);
    for(int i=0; i<count; i++)
    {
        SetFieldC(in[i], i);
    }
}
/*  , (0 to 255)*/
void CopyOutFieldC(uint8_t* out, int len)
{
    int count = ((len < 5) ? len : 5);
    for(int i=0; i<count; i++)
    {
        out[i] = GetFieldC(i);
    }
}
/*  , (0 to 255)*/
uint8_t* FieldC()
{
    return (uint8_t*)&m_data[6];
}""")
        expected.append("""\
/*  , (-2147483648 to 2147483647)*/
void CopyInFieldS2_Member1(const int32_t* in, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        SetFieldS2_Member1(in[i], i);
    }
}
/*  , (-2147483648 to 2147483647)*/
void CopyOutFieldS2_Member1(int32_t* out, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        out[i] = GetFieldS2_Member1(i);
    }
}
""")
        expected.append("""\
/*  , (DBL_MIN to DBL_MAX)*/
void CopyInFieldS2_Member2(const double* in, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        SetFieldS2_Member2(in[i], i);
    }
}
/*  , (DBL_MIN to DBL_MAX)*/
void CopyOutFieldS2_Member2(double* out, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        out[i] = GetFieldS2_Member2(i);
    }
}
""")
        expected.append("""\
/* Test Field G, array of bitfields , (0 to 65535)*/
void CopyInFieldG(const uint16_t* in, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        SetFieldG(in[i], i);
    }
}
/* Test Field G, array of bitfields , (0 to 65535)*/
void CopyOutFieldG(uint16_t* out, int len)
{
    int count = ((len < 3) ? len : 3);
    for(int i=0; i<count; i++)
    {
        out[i] = GetFieldG(i);
    }
}
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__ 
/* Test Field G, array of bitfields , (0 to 65535)*/
uint16_t* FieldG()
{
    return (uint16_t*)&m_data[66];
}
#endif
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
        expected = 'enum class EnumA {OptionA = 1, OptionB = 2, OptionC = 4, OptionD = 5};\n'
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
        expected.append("for (int i=0; i<3; i++)\n    SetBitsD(7.1, i);")
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
