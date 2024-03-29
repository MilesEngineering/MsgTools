#!/usr/bin/env python3
import unittest
import traceback

from msgtools.lib.messaging import Messaging

import msgtools.lib.msgcsv as msgcsv
import msgtools.lib.msgjson as msgjson

class TestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print ("----------- Running setup")
        Messaging.LoadAllMessages()

    def test_dict(self):
        msgname = "Network.Connect"
        msgid = Messaging.MsgIDFromName[msgname]

        msgid2 = "0xffffff01"
        msgname2 = Messaging.MsgNameFromID[msgid]
        self.assertMultiLineEqual(msgname, msgname2)
        self.assertEqual(msgid, msgid2)
    
        self.PrintDictionary()

    def test_accessors(self):
        msgclass = Messaging.MsgClassFromName["Network.Connect"]
        sameMsgClass = Messaging.Messages.Network.Connect
        self.assertEqual(msgclass, sameMsgClass)

        expected = "Testing"
        testMsg = msgclass()
        Messaging.set(testMsg, msgclass.fields[0], expected)
        observed = testMsg.GetName()
        self.assertMultiLineEqual(expected, observed)
        
        expected="MoreTesting"
        testMsg.SetName(expected)
        observed=Messaging.get(testMsg, msgclass.fields[0])
        self.assertMultiLineEqual(expected, observed)

    def PrintDictionary(self):
        width=10
        print("")
        print("Msg Dictionary")
        print("----------------------")
        print("%-10s: ID" %"Name")
        for msgId, name in Messaging.MsgNameFromID.items():
             print("%-10s: %s" % (name, msgId))
             msgClass = Messaging.MsgClassFromName[name]
             self.PrintAccessors(msgClass)
        print("")

    # example of how to call a method given by reflection
    def PrintAccessors(self, msgClass):
        msg = msgClass()
        for fieldInfo in msgClass.fields:
            txt = "body.%s.%s: " % (msgClass.__name__, fieldInfo.name)
            if(fieldInfo.count == 1):
                txt += str(Messaging.get(msg, fieldInfo))
            else:
                for i in range(0,fieldInfo.count):
                    #print("body.",msgClass.__name__, ".", method.__name__, "[",i,"] = ", method(msg,i), " #", method.__doc__, "in", method.units)
                    txt += str(Messaging.get(msg, fieldInfo, i))
                    if(i < fieldInfo.count - 1):
                        txt += ", "
            txt += " # "+fieldInfo.description+" in " + fieldInfo.units
            print(txt)
    
    def info(self, testCase, tcNum, fieldName):
        ret  = "\nTest Case #" + str(tcNum) + "\n"
        ret += "'%s' != '%s'\n" % (str(testCase[0]), str(testCase[1]))
        ret += "at field " + fieldName
        return ret

    def test_csv_and_dict(self):
        testData = [
         ('TestCase4 ;',                                                {"TestCase4": {}, "hdr" : {"DataLength": ";"}}),
         ('TestCase4 ',                                                 {"TestCase4": {"A":0, "B": [0,0,0], "C": [0,0,0], "D": ""}}),
         ('TestCase4 2, 2,3,4,5,6,7,8,9,10,11, 12,13,14,ei;ght',        {"TestCase4": {"A":2, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "ei;ght"}}),
         ("TestCase4 3, 2;",                                            {"TestCase4": {"A":3, "B": [2]}, "hdr" : {"DataLength": ";"}}),
         ("TestCase4 4, 0x0203 ;",                                      {"TestCase4": {"A":4, "B": [2,3]}, "hdr" : {"DataLength": ";"}}),
         ("TestCase4 5, 0x020304, 0x00050006 ;",                        {"TestCase4": {"A":5, "B": [2,3,4], "C": [5,6]}, "hdr" : {"DataLength": ";"}}),
         ("TestCase4 6, 2",                                             {"TestCase4": {"A":6, "B": [2, 0,0],"C": [0,0,0], "D": ""}}), # note without semicolon, unspecified fields have default values
         ("TestCase4 7, 0x020304, 5,6,0x07",                            {"TestCase4": {"A":7, "B": [2,3,4], "C": [5,6,7], "D": ""}}),
         ("TestCase4 8, 2,3,4,5,6,7,8,9,10,11, 12,13,14, 0x8",          {"TestCase4": {"A":8, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "0x8"}}),
         ("TestCase4 9, 2,3,4,5,6,7,8,9,10,11, 12,13,14, eight",        {"TestCase4": {"A":9, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eight"}}),
         ('TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, "eight"',      {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eight"}}),
         ('TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, "eig,ht"',     {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eig,ht"}}),
         ("TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, ei ght",       {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "ei ght"}}),
         ("TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, 0x8;",         {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "0x8"}, "hdr" : {"DataLength": ";"}}),
         ("TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, eight;",       {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eight"}, "hdr" : {"DataLength": ";"}}),
         ('TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, "eight;"',     {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eight;"}}),
         ('TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, "eig,ht";',    {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "eig,ht"}, "hdr" : {"DataLength": ";"}}),
         ("TestCase4 1, 2,3,4,5,6,7,8,9,10,11, 12,13,14, ei ght;",      {"TestCase4": {"A":1, "B": [2,3,4,5,6,7,8,9,10,11], "C": [12,13,14], "D": "ei ght"}, "hdr" : {"DataLength": ";"}}),
         ("TestCase1, 1,2,13,14, 15,16,  17,0.0,OptionA,1;",      {"TestCase1": {"FieldA":1, "FieldB": 2, "FieldC": [13,14,15,16,17], "BitsA": "0.0", "BitsB": "OptionA", "BitsC":1}, "hdr" : {"DataLength": ";"}}),
         ("TestCase1, 2, 3, 13, 14, 15, 16, 17, 0.0, 0x1, 1;",      {"TestCase1": {"FieldA":2, "FieldB": 3, "FieldC": [13,14,15,16,17], "BitsA": "0.0", "BitsB": "0x1", "BitsC":1}, "hdr" : {"DataLength": ";"}})]
        commaTestData = []
        for tc in testData:
            newTestCase = (tc[0].replace("TestCase4 ", "TestCase4,"), tc[1])
            commaTestData.append(newTestCase)
        testData.extend(commaTestData)

        tcNum = 0
        for tc in testData:
            try:
                msg = msgcsv.csvToMsg(tc[0])
                j = msgjson.toJson(msg)
                msg2 = msgjson.dictToMsg(tc[1])
                #print("csv is " + tc[0])
                self.assertEqual(msg.hdr.GetDataLength(), msg2.hdr.GetDataLength(), self.info(tc, tcNum, "hdr.DataLength"))
                #print("json of csv is " + j)
                for fieldInfo in type(msg).fields:
                    if(fieldInfo.count == 1):
                        if not fieldInfo.exists(msg):
                            break
                        
                        if len(fieldInfo.bitfieldInfo) == 0:
                            self.assertEqual(Messaging.get(msg, fieldInfo), Messaging.get(msg2, fieldInfo), self.info(tc, tcNum, fieldInfo.name))
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                self.assertEqual(Messaging.get(msg, bitInfo), Messaging.get(msg2, bitInfo), self.info(tc, tcNum, fieldInfo.name+"."+bitInfo.name))
                    else:
                        exit_loop = False
                        for i in range(0,fieldInfo.count):
                            if not fieldInfo.exists(msg, i):
                                exit_loop = True
                                break
                            self.assertEqual(Messaging.get(msg, fieldInfo, i), Messaging.get(msg2, fieldInfo, i), self.info(tc, tcNum, fieldInfo.name+"["+str(i)+"]"))
                        if exit_loop:
                            break
            except AssertionError:
                print("test_csv_and_dict test case %d" % (tcNum))
                msg1 = msgcsv.csvToMsg(tc[0])
                print(msg1)
                msg2 = msgjson.dictToMsg(tc[1])
                print(msg2)
                raise
            except:
                print("Exception on test case %d, [%s] != [%s]" % (tcNum, tc[0], tc[1]))
                msg1 = msgcsv.csvToMsg(tc[0])
                print(msg1)
                msg2 = msgjson.dictToMsg(tc[1])
                print(msg2)
                print(traceback.format_exc())
                self.assertEqual(True, False)
            tcNum += 1
            #print("\n\n")

    def test_long_substr(self):
        testData = [
         (['123', 'abc'], ''),
         (['123', '12'], '12'),
         (['12', '123'], '12'),
         (['123', '123'], '123'),
         (['123', '124'], '12'),
         (['123', '12456', '123'], '12')
        ]
        tcNum = 0
        for tc in testData:
            try:
                observed = msgcsv.long_substr(tc[0])
                expected = tc[1]
                self.assertEqual(observed, expected)
            except AssertionError:
                print("test_long_substr test case %d" % (tcNum))
                raise
            except:
                print("Exception on test case %d, [%s] != [%s]" % (tcNum, tc[0], tc[1]))
                print(traceback.format_exc())
                self.assertEqual(True, False)
            tcNum += 1
        
    def test_tab_complete(self):
        testData = [
         ('TestC',     'TestCase', 'TestCase1\nTestCase2\nTestCase3\nTestCase4'),
         ('TestCa',    'TestCase', 'TestCase1\nTestCase2\nTestCase3\nTestCase4'),
         ('TestCase',  'TestCase', 'TestCase1\nTestCase2\nTestCase3\nTestCase4'),
         ('TestCase3', 'TestCase3,', 'TestCase3'),
         ('TestCase3,', None, 'TestCase3, Latitude, Field1[3], BitsA, BitsB, BitsC, Field3, Field4'),
         ('TestCase3,1', None, 'Field1(m/s)# Test Field 1'), # csv specified first array elem of Field1
         ('TestCase3,1,2', None, 'Field1(m/s)# Test Field 1'), # csv specified 2 array elems of Field1
         ('TestCase3,1,2,3', None, 'Field1(m/s)# Test Field 1'), #  csv specified all 3 array elems of Field1
         ('TestCase3,1,2,3,4', None, 'BitsA(m/s)') # csv specified all of Field1 and first bitfield of Field2
        ]
        tcNum = 0
        for tc in testData:
            try:
                autocomplete, help = msgcsv.csvHelp(tc[0])
                self.assertEqual(autocomplete, tc[1])
                self.assertEqual(help, tc[2])
            except AssertionError:
                print("test_tab_complete test case %d" % (tcNum))
                raise
            except:
                print("Exception on test case %d, [%s] != [%s]" % (tcNum, tc[0], tc[1]))
                print(traceback.format_exc())
                self.assertEqual(True, False)
            tcNum += 1

def main(args=None):
    unittest.main()

# main starts here
if __name__ == '__main__':
    main()
