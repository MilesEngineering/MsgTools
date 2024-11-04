from .messaging import Messaging

# for conversion to JSON
from collections import OrderedDict
import json
import struct

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
            if not fieldInfo.exists(msg):
                break
            if len(fieldInfo.bitfieldInfo) == 0:
                pythonObj[fieldInfo.name] = Messaging.get(msg, fieldInfo)
            else:
                for bitInfo in fieldInfo.bitfieldInfo:
                    pythonObj[bitInfo.name] = Messaging.get(msg, bitInfo)
        else:
            if len(fieldInfo.bitfieldInfo) == 0:
                arrayList = []
                terminate = 0
                for i in range(0,fieldInfo.count):
                    if not fieldInfo.exists(msg, i):
                        terminate = 1
                        break
                    arrayList.append(Messaging.get(msg, fieldInfo, i))
                pythonObj[fieldInfo.name] = arrayList
                if terminate:
                    break
            else:
                # Arrays-of-structs acting like parallel arrays.
                for bitInfo in fieldInfo.bitfieldInfo:
                    arrayList = []
                    for i in range(0,fieldInfo.count):
                        if not fieldInfo.exists(msg, i):
                            break
                        arrayList.append(Messaging.get(msg, bitInfo, i))
                    pythonObj[bitInfo.name] = arrayList

    return {msg.MsgName() : pythonObj}

def toJson(msg, includeHeader=False):
    return json.dumps(toDict(msg,includeHeader))

def jsonToMsg(jsonString, ignore_invalid=False):
    d = json.loads(jsonString)
    return dictToMsg(d, ignore_invalid)

def dictToMsg(d, ignore_invalid=False):
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
                    if "Time" in fieldDict["hdr"]:
                        msg.hdr.SetTime(fieldDict["hdr"]["Time"])
                    terminationLen = handle_header(fieldDict["hdr"])
                    continue
                fieldInfo = Messaging.findFieldInfo(msgClass.fields, fieldName)
                if fieldInfo == None:
                    if ignore_invalid:
                        if ignore_invalid != "silent":
                            print("Ignoring invalid field %s.%s" % (msgName, fieldName))
                        continue
                    else:
                        raise KeyError("Invalid field %s for message %s" % (fieldName, msgName))
                fieldValue = fieldDict[fieldName]
                if isinstance(fieldValue, list):
                    #print(fieldName + " list type is " + type(fieldValue))
                    for i in range(0,len(fieldValue)):
                        try:
                            Messaging.set(msg, fieldInfo, fieldValue[i], i)
                        except struct.error as e:
                            print(e)
                            break
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
    # Shorten the message if necessary.
    if terminationLen != None and terminationLen < msg.hdr.GetDataLength():
        msg.hdr.SetDataLength(terminationLen)
    return msg

# return list of metadata for fields
def jsonHeader(msg):
    ret = ""
    msgClass = Messaging.MsgClass(msg.hdr)
    for fieldInfo in msgClass.fields:
        e = None
        if len(fieldInfo.enum) > 0:
            e = fieldInfo.enum[0] # list element 0 is forward mapping (list element 1 is reverse mapping)
        pythonObj = OrderedDict()
        pythonObj["name"]=fieldInfo.name
        pythonObj["type"]=fieldInfo.type
        pythonObj["units"]=fieldInfo.units
        pythonObj["min"]=fieldInfo.minVal
        pythonObj["max"]=fieldInfo.maxVal
        pythonObj["description"]=fieldInfo.description
        pythonObj["count"]=fieldInfo.count
        #pythonObj["enum"]=e
        ret += json.dumps({"FIELD_METADATA."+msg.MsgName() : pythonObj}) + "\n"
        if len(fieldInfo.bitfieldInfo) > 0:
            for bitInfo in fieldInfo.bitfieldInfo:
                e = None
                if len(bitInfo.enum) > 0:
                    e = bitInfo.enum[0] # list element 0 is forward mapping (list element 1 is reverse mapping)
                pythonObj = OrderedDict()
                pythonObj["name"]=bitInfo.name
                pythonObj["type"]=bitInfo.type
                pythonObj["units"]=bitInfo.units
                pythonObj["min"]=bitInfo.minVal
                pythonObj["max"]=bitInfo.maxVal
                pythonObj["description"]=bitInfo.description
                pythonObj["count"]=bitInfo.count
                #pythonObj["enum"]=e

                ret += json.dumps({"FIELD_METADATA."+msg.MsgName() : pythonObj}) + "\n"
    return ret