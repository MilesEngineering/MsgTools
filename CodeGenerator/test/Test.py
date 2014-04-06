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
        self.msgIDL = """
Messages:
  - Name: MsgA
    Description: blah
    Fields:
      - Name: FieldA
        Type: uint32
        DefaultValue: 1
      - Name: FieldB
        Type: uint16
        DefaultValue: 2
      - Name: FieldC
        Type: uint8
        DefaultValue: 3
        """
        self.msgDict = yaml.load(self.msgIDL)

    def test_accessors(self):
        expected = """\
uint32_t GetFieldA() { return *(uint32_t*)&m_data[0]; }
uint16_t GetFieldB() { return *(uint16_t*)&m_data[4]; }
uint8_t GetFieldC() { return *(uint8_t*)&m_data[6]; }
void SetFieldA(uint32_t& value) { *(uint32_t*)&m_data[0] = value; }
void SetFieldB(uint16_t& value) { *(uint16_t*)&m_data[4] = value; }
void SetFieldC(uint8_t& value) { *(uint8_t*)&m_data[6] = value; }
"""
        observed = language.accessors(MsgParser.Messages(self.msgDict)[0])
        self.assertMultiLineEqual(expected, observed)
        with self.assertRaises(IndexError):
            language.accessors(MsgParser.Messages(self.msgDict)[1])

    def test_msgNames(self):
        expected = "MsgA"
        observed = MsgParser.msgName(MsgParser.Messages(self.msgDict)[0])
        self.assertMultiLineEqual(expected, observed)
        with self.assertRaises(IndexError):
            MsgParser.msgName(MsgParser.Messages(self.msgDict)[1])

if __name__ == '__main__':
    unittest.main()
