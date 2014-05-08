import sys
sys.path.append(".")
import Messaging
import ctypes

# this prints all the message names and ids that are defined
def PrintDictionary():
    width=10
    print("")
    print("Msg Dictionary")
    print("----------------------")
    print("%-10s: ID" %"Name")
    for msgId, name in msgLib.MsgNameFromID.items():
         print("%-10s: %s" % (name, msgId))
    print("")

# example of how to call a method given by reflection
def PrintAccessors(msgName, msg):
    msgClass = msgLib.MsgClassFromName[msgName]
    methods = msgLib.MsgAccessors(msgClass)
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

# main starts here
if __name__ == '__main__':
    msgLib = Messaging.Messaging("../CodeGenerator/obj/Python", 1)
    PrintDictionary()
    msgname = "Connect"
    msgid = msgLib.MsgIDFromName[msgname]
    print("msgname for",msgname,"class is ",msgid)

    msgid = "0xffffff01"
    msgname = msgLib.MsgNameFromID[msgid]
    msgclass = msgLib.MsgClassFromName[msgname]
    print("msgid is",msgid,"for class",msgname)
    #print "\n\n",vars(Messaging),"\n";

    testbuf = msgclass.Create()
    msgclass.SetName(testbuf, "Testing")

    #print(vars(msgLib.Connect))
    PrintAccessors("Connect", testbuf)