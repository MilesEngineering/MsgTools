import unittest
import sys
sys.path.append(".")
import Messaging
import ctypes

class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print ("----------- Running setup")
        cls.msgLib = Messaging.Messaging("../CodeGenerator/obj/Python", 0)
        #cls.PrintDictionary()

    def test_dict(self):
        msgname = "Connect"
        msgid = self.msgLib.MsgIDFromName[msgname]

        msgid2 = "0xffffff01"
        msgname2 = self.msgLib.MsgNameFromID[msgid]
        self.assertMultiLineEqual(msgname, msgname2)
        self.assertEqual(msgid, msgid2)
    
    def test_accessors(self):
        msgclass = self.msgLib.MsgClassFromName["Connect"]

        expected = "Testing"
        testbuf = msgclass.Create()
        self.msgLib.MsgMutators(msgclass)[0](testbuf, expected)
        observed = self.msgLib.Connect.Connect.GetName(testbuf)
        self.assertMultiLineEqual(expected, observed)
        
        expected="MoreTesting"
        msgclass.SetName(testbuf, expected)
        observed=self.msgLib.MsgAccessors(msgclass)[0](testbuf)
        self.assertMultiLineEqual(expected, observed)

    def PrintDictionary(self):
        width=10
        print("")
        print("Msg Dictionary")
        print("----------------------")
        print("%-10s: ID" %"Name")
        for msgId, name in self.msgLib.MsgNameFromID.items():
             print("%-10s: %s" % (name, msgId))
        print("")

    # example of how to call a method given by reflection
    def PrintAccessors(self, msgName, msg):
        msgClass = self.msgLib.MsgClassFromName[msgName]
        methods = self.msgLib.MsgAccessors(msgClass)
        for method in methods:
            txt = "body.%s.%s: " % (msgClass.__name__, method.__name__)
            if(method.count == 1):
                txt += str(method(msg))
            else:
                for i in range(0,method.count):
                    #print("body.",msgClass.__name__, ".", method.__name__, "[",i,"] = ", method(msg,i), " #", method.__doc__, "in", method.units)
                    txt += ", " + str(method(msg,i))
            txt += " # "+method.__doc__+" in " + method.units
            print(txt)

if __name__ == '__main__':
    unittest.main()
