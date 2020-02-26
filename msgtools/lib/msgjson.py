from .messaging import Messaging

# for conversion to JSON
from collections import OrderedDict
import json

def toJson(msg, includeHeader=False):
    pythonObj = OrderedDict()
    if includeHeader:
        pythonObj['hdr'] = OrderedDict()
        for fieldInfo in msg.hdr.fields:
            if(fieldInfo.count == 1):
                if len(fieldInfo.bitfieldInfo) == 0:
                    pythonObj['hdr'][fieldInfo.name] = str(Messaging.get(msg.hdr, fieldInfo))
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        pythonObj['hdr'][bitInfo.name] = str(Messaging.get(msg.hdr, bitInfo))
            else:
                arrayList = []
                terminate = 0
                for i in range(0,fieldInfo.count):
                    arrayList.append(str(Messaging.get(msg.hdr, fieldInfo, i)))
                pythonObj['hdr'][fieldInfo.name] = arrayList

    msgClass = Messaging.MsgClass(msg.hdr)
    for fieldInfo in msgClass.fields:
        if(fieldInfo.count == 1):
            #TODO Broken for arrays-of-structs acting like parallel arrays!
            if not fieldInfo.exists(msg):
                break
            if len(fieldInfo.bitfieldInfo) == 0:
                pythonObj[fieldInfo.name] = str(Messaging.get(msg, fieldInfo))
            else:
                for bitInfo in fieldInfo.bitfieldInfo:
                    pythonObj[bitInfo.name] = str(Messaging.get(msg, bitInfo))
        else:
            arrayList = []
            terminate = 0
            for i in range(0,fieldInfo.count):
                #TODO Broken for arrays-of-structs acting like parallel arrays!
                if not fieldInfo.exists(msg, i):
                    terminate = 1
                    break
                arrayList.append(str(Messaging.get(msg, fieldInfo, i)))
            pythonObj[fieldInfo.name] = arrayList
            if terminate:
                break

    return json.dumps({msg.MsgName() : pythonObj})

def jsonToMsg(jsonString):
    terminationLen = None
    if "hdr" in jsonString:
        fieldJson = jsonString["hdr"]
        for fieldName in fieldJson:
            if fieldName == "DataLength":
                if fieldJson[fieldName] == ";":
                    terminationLen = 0
                else:
                    terminationLen = int(fieldJson[fieldName])
    for msgName in jsonString:
        if msgName == "hdr":
            # hdr handled above, *before* message body
            pass
        else:
            fieldJson = jsonString[msgName]
            msgClass = Messaging.MsgClassFromName[msgName]
            msg = msgClass()
            for fieldName in fieldJson:
                fieldInfo = Messaging.findFieldInfo(msgClass.fields, fieldName)
                fieldValue = fieldJson[fieldName]
                if isinstance(fieldValue, list):
                    #print(fieldName + " list type is " + str(type(fieldValue)))
                    for i in range(0,len(fieldValue)):
                        Messaging.set(msg, fieldInfo, fieldValue[i], i)
                        if terminationLen != None:
                            #TODO Broken for arrays-of-structs acting like parallel arrays!
                            terminationLen = max(terminationLen, fieldInfo.end_location(i))
                elif isinstance(fieldValue, dict):
                    #print(fieldName + " dict type is " + str(type(fieldValue)))
                    if fieldInfo.bitfieldInfo:
                        pass
                    else:
                        pass
                else:
                    #print(str(type(fieldValue)) + " " + fieldName + ", calling set with " + str(fieldValue))
                    Messaging.set(msg, fieldInfo, fieldValue)
                    if terminationLen != None:
                        if fieldInfo.type == "string":
                            #TODO Broken for arrays-of-structs acting like parallel arrays!
                            terminationLen = max(terminationLen, fieldInfo.end_location(len(fieldValue)-1))
                        else:
                            #TODO Broken for arrays-of-structs acting like parallel arrays!
                            terminationLen = max(terminationLen, fieldInfo.end_location())
    if terminationLen != None:
        msg.hdr.SetDataLength(terminationLen)
    return msg
