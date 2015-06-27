#!/usr/bin/env python3
import unittest
import sys
sys.path.append("..")
import Messaging
import ctypes

class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print ("----------- Running setup")
        cls.msgLib = Messaging.Messaging("../../obj/CodeGenerator/Python", 0)

    def test_dict(self):
        msgname = "Connect"
        msgid = self.msgLib.MsgIDFromName[msgname]

        msgid2 = "0xffffff01"
        msgname2 = self.msgLib.MsgNameFromID[msgid]
        self.assertMultiLineEqual(msgname, msgname2)
        self.assertEqual(msgid, msgid2)
    
        self.PrintDictionary()

    def test_accessors(self):
        msgclass = self.msgLib.MsgClassFromName["Connect"]

        expected = "Testing"
        testbuf = msgclass.Create()
        msgclass.set(testbuf, msgclass.fields[0], expected)
        observed = self.msgLib.Connect.Connect.GetName(testbuf)
        self.assertMultiLineEqual(expected, observed)
        
        expected="MoreTesting"
        msgclass.SetName(testbuf, expected)
        observed=msgclass.get(testbuf, msgclass.fields[0])
        self.assertMultiLineEqual(expected, observed)

    def PrintDictionary(self):
        width=10
        print("")
        print("Msg Dictionary")
        print("----------------------")
        print("%-10s: ID" %"Name")
        for msgId, name in self.msgLib.MsgNameFromID.items():
             print("%-10s: %s" % (name, msgId))
             msgClass = self.msgLib.MsgClassFromName[name]
             self.PrintAccessors(msgClass)
        print("")

    # example of how to call a method given by reflection
    def PrintAccessors(self, msgClass):
        msg = msgClass.Create()
        for fieldInfo in msgClass.fields:
            txt = "body.%s.%s: " % (msgClass.__name__, fieldInfo.name)
            if(fieldInfo.count == 1):
                txt += str(msgClass.get(msg, fieldInfo))
            else:
                for i in range(0,fieldInfo.count):
                    #print("body.",msgClass.__name__, ".", method.__name__, "[",i,"] = ", method(msg,i), " #", method.__doc__, "in", method.units)
                    txt += str(msgClass.get(msg, fieldInfo, i))
                    if(i < fieldInfo.count - 1):
                        txt += ", "
            txt += " # "+fieldInfo.description+" in " + fieldInfo.units
            print(txt)

if __name__ == '__main__':
    unittest.main()
