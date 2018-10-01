from .messaging import Messaging

# for conversion to JSON
from collections import OrderedDict
import json

def toJson(msg):
    msgClass = Messaging.MsgClass(msg.hdr)
    pythonObj = OrderedDict()
    for fieldInfo in msgClass.fields:
        if(fieldInfo.count == 1):
            if msg.hdr.GetDataLength() < int(fieldInfo.get.offset) + int(fieldInfo.get.size):
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
                if msg.hdr.GetDataLength() < int(fieldInfo.get.offset) + i*int(fieldInfo.get.size):
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
                            terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size)*(i+1))
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
                            terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size) * len(fieldValue))
                        else:
                            terminationLen = max(terminationLen, int(fieldInfo.get.offset) + int(fieldInfo.get.size))
    if terminationLen != None:
        msg.hdr.SetDataLength(terminationLen)
    return msg
