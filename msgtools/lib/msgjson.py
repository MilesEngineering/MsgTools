from .messaging import Messaging

# for conversion to JSON
from collections import OrderedDict
import json

def toDict(msg, includeHeader=False):
    pythonObj = OrderedDict()
    if includeHeader:
        pythonObj['hdr'] = OrderedDict()
        for fieldInfo in msg.hdr.fields:
            if(fieldInfo.count == 1):
                if len(fieldInfo.bitfieldInfo) == 0:
                    pythonObj['hdr'][fieldInfo.name] = Messaging.get(msg.hdr, fieldInfo)
                else:
                    for bitInfo in fieldInfo.bitfieldInfo:
                        pythonObj['hdr'][bitInfo.name] = Messaging.get(msg.hdr, bitInfo)
            else:
                arrayList = []
                terminate = 0
                for i in range(0,fieldInfo.count):
                    arrayList.append(Messaging.get(msg.hdr, fieldInfo, i))
                pythonObj['hdr'][fieldInfo.name] = arrayList

    msgClass = Messaging.MsgClass(msg.hdr)
    for fieldInfo in msgClass.fields:
        if(fieldInfo.count == 1):
            #TODO Broken for arrays-of-structs acting like parallel arrays!
            if not fieldInfo.exists(msg):
                break
            if len(fieldInfo.bitfieldInfo) == 0:
                pythonObj[fieldInfo.name] = Messaging.get(msg, fieldInfo)
            else:
                for bitInfo in fieldInfo.bitfieldInfo:
                    pythonObj[bitInfo.name] = Messaging.get(msg, bitInfo)
        else:
            arrayList = []
            terminate = 0
            for i in range(0,fieldInfo.count):
                #TODO Broken for arrays-of-structs acting like parallel arrays!
                if not fieldInfo.exists(msg, i):
                    terminate = 1
                    break
                arrayList.append(Messaging.get(msg, fieldInfo, i))
            pythonObj[fieldInfo.name] = arrayList
            if terminate:
                break
    return {msg.MsgName() : pythonObj}

def toJson(msg, includeHeader=False):
    return json.dumps(toDict(msg,includeHeader))

def jsonToMsg(jsonString):
    d = json.loads(jsonString)
    return dictToMsg(d)

def dictToMsg(d):
    terminationLen = None
    def handle_header(hdrDict):
        length = None
        for fieldName in hdrDict:
            if fieldName == "DataLength":
                if hdrDict[fieldName] == ";":
                    length = 0
                else:
                    length = int(hdrDict[fieldName])
        return length
    if "hdr" in d:
        hdrDict = d["hdr"]
        terminationLen = handle_header(hdrDict)
    for msgName in d:
        if msgName == "hdr":
            # hdr handled above, *before* message body
            pass
        else:
            fieldDict = d[msgName]
            msgClass = Messaging.MsgClassFromName[msgName]
            msg = msgClass()
            for fieldName in fieldDict:
                if fieldName == "hdr":
                    terminationLen = handle_header(fieldDict["hdr"])
                    continue
                fieldInfo = Messaging.findFieldInfo(msgClass.fields, fieldName)
                if fieldInfo == None:
                    raise KeyError("Invalid field %s for message %s" % (fieldName, msgName))
                fieldValue = fieldDict[fieldName]
                if isinstance(fieldValue, list):
                    #print(fieldName + " list type is " + type(fieldValue))
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
