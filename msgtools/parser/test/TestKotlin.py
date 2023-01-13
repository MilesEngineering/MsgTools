#!/usr/bin/env python3
import unittest
import yaml
import sys
sys.path.append("../../..")
import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import PatchStructs
sys.path.append("../kotlin")
import language

class TestKotlin(unittest.TestCase):
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
fun getFieldA(): UInt {
    return data.getUInt(0, true)
}""")
        expected.append("""\
//  , (0 to 2147483647)
fun getFABitsA(): UInt {
    return ((getFieldA().toInt() ushr 0) and 0x7fffffff).toUInt()
}""")
        expected.append("""\
//  , (0 to 65535)
fun getFieldB(): UShort {
    return data.getUShort(4, true)
}""")
        expected.append("""\
//  , (0 to 255)
fun getFieldC(index: Int): UByte {
    return data.getUByte(6 + index*1, true)
}""")
        expected.append("""\
//  , (0 to 255)
fun getFieldD(): UByte {
    return data.getUByte(11, true)
}""")
        expected.append("""\
//  , (0.0 to 215.355)
fun getBitsA(): Float {
    val valI = ((getFieldD().toInt() ushr 0) and 0xf).toFloat()
    val valD = (valI.toInt().toDouble() * 14.357f).toFloat()
    return valD
}""")
        expected.append("""\
//  , (0 to 7)
fun getBitsB(): UByte {
    return ((getFieldD().toInt() ushr 4) and 0x7).toUByte()
}""")
        expected.append("""\
//  , (0 to 1)
fun getBitsC(): UByte {
    return ((getFieldD().toInt() ushr 7) and 0x1).toUByte()
}""")
        expected.append("""\
//  , (0.0 to 10.0)
fun getFieldE(): Float {
    return data.getFloat(12, true)
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
fun getFieldS1_Member1(): Int {
    return data.getInt(16, true)
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
fun getFieldS1_Member2(): Double {
    return data.getDouble(20, true)
}""")
        expected.append("""\
//  , (1.828 to 176946.328)
fun getFieldF(): Float {
    val valI : UShort = data.getUShort(28, true)
    val valD = ((valI.toInt().toDouble() * 2.7f) + 1.828f).toFloat()
    return valD
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
fun getFieldS2_Member1(index: Int): Int {
    return data.getInt(30 + index*12, true)
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
fun getFieldS2_Member2(index: Int): Double {
    return data.getDouble(34 + index*12, true)
}""")
        expected.append("""\
// Test Field G, array of bitfields , (0 to 65535)
fun getFieldG(index: Int): UShort {
    return data.getUShort(66 + index*2, true)
}""")
        expected.append("""\
//  m/s, (0.0 to 215.355)
fun getBitsD(): Float {
    val valI = ((getFieldG().toInt() ushr 0) and 0xf).toFloat()
    val valD = (valI.toInt().toDouble() * 14.357f).toFloat()
    return valD
}""")
        expected.append("""\
//  m/s2, (0 to 511)
fun getBitsE(): UShort {
    return ((getFieldG().toInt() ushr 4) and 0x1ff).toUShort()
}""")
        expected.append("""\
//  m/s, (0 to 4294967295)
fun setFieldA(value: UInt) {
    data.putUInt(0, value, true)
}""")
        expected.append("""\
//  , (0 to 2147483647)
fun setFABitsA(value: UInt) {
    var valI = getFieldA().toInt() // read
    valI = valI and (0x7fffffff shl 0).inv() // clear our bits
    valI = valI or ((value.toInt() and 0x7fffffff) shl 0) // set our bits
    setFieldA(valI.toUInt()) // write
}""")
        expected.append("""\
//  , (0 to 65535)
fun setFieldB(value: UShort) {
    data.putUShort(4, value, true)
}""")
        expected.append("""\
//  , (0 to 255)
fun setFieldC(value: UByte, index: Int) {
    data.putUByte(6 + index*1, value, true)
}""")
        expected.append("""\
//  , (0 to 255)
fun setFieldD(value: UByte) {
    data.putUByte(11, value, true)
}""")
        expected.append("""\
//  , (0.0 to 215.355)
fun setBitsA(value: Float) {
    var valI = getFieldD().toInt() // read
    valI = valI and (0xf shl 0).inv() // clear our bits
    valI = valI or (((value / 14.357f).toInt() and 0xf) shl 0) // set our bits
    setFieldD(valI.toUByte()) // write
}""")
        expected.append("""\
//  , (0 to 7)
fun setBitsB(value: UByte) {
    var valI = getFieldD().toInt() // read
    valI = valI and (0x7 shl 4).inv() // clear our bits
    valI = valI or ((value.toInt() and 0x7) shl 4) // set our bits
    setFieldD(valI.toUByte()) // write
}""")
        expected.append("""\
//  , (0 to 1)
fun setBitsC(value: UByte) {
    var valI = getFieldD().toInt() // read
    valI = valI and (0x1 shl 7).inv() // clear our bits
    valI = valI or ((value.toInt() and 0x1) shl 7) // set our bits
    setFieldD(valI.toUByte()) // write
}""")
        expected.append("""\
//  , (0.0 to 10.0)
fun setFieldE(value: Float) {
    data.putFloat(12, value, true)
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
fun setFieldS1_Member1(value: Int) {
    data.putInt(16, value, true)
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
fun setFieldS1_Member2(value: Double) {
    data.putDouble(20, value, true)
}""")
        expected.append("""\
//  , (1.828 to 176946.328)
fun setFieldF(value: Float) {
    data.putUShort(28, ((value - 1.828f) / 2.7f).toUShort(), true)
}""")
        expected.append("""\
//  , (-2147483648 to 2147483647)
fun setFieldS2_Member1(value: Int, index: Int) {
    data.putInt(30 + index*12, value, true)
}""")
        expected.append("""\
//  , (DBL_MIN to DBL_MAX)
fun setFieldS2_Member2(value: Double, index: Int) {
    data.putDouble(34 + index*12, value, true)
}""")
        expected.append("""\
// Test Field G, array of bitfields , (0 to 65535)
fun setFieldG(value: UShort, index: Int) {
    data.putUShort(66 + index*2, value, true)
}""")
        expected.append("""\
//  m/s, (0.0 to 215.355)
fun setBitsD(value: Float) {
    var valI = getFieldG().toInt() // read
    valI = valI and (0xf shl 0).inv() // clear our bits
    valI = valI or (((value / 14.357f).toInt() and 0xf) shl 0) // set our bits
    setFieldG(valI.toUShort()) // write
}""")
        expected.append("""\
//  m/s2, (0 to 511)
fun setBitsE(value: UShort) {
    var valI = getFieldG().toInt() // read
    valI = valI and (0x1ff shl 4).inv() // clear our bits
    valI = valI or ((value.toInt() and 0x1ff) shl 4) // set our bits
    setFieldG(valI.toUShort()) // write
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
        expected = '''enum class EnumA(override val value: Long): MessageEnum {
    OptionA(1), OptionB(2), OptionC(4), OptionD(5);
    companion object {
        fun construct(value: Long): EnumA {
            return values().first { it.value == value }
        }
    }
}
'''
        observed = language.enums(MsgParser.Enums(self.msgDict))
        self.assertMultiLineEqual(expected, observed)
    
    def test_initCode(self):
        expected = []
        expected.append("setFieldA(1u)")
        expected.append("setFieldB(2u)")
        expected.append("for (i in 0 until 5) {\n    setFieldC(3u, i)\n}\n")
        expected.append("setBitsA(7.1f)")
        expected.append("setBitsC(1u)")
        expected.append("setFieldE(3.14159f)")
        expected.append("setFieldF(3.14f)")
        expected.append("setBitsD(7.1f)")
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
