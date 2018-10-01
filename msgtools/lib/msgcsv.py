from .messaging import Messaging

# for reading CSV
import csv

def toCsv(msg):
    ret = ""
    for fieldInfo in Messaging.MsgClass(msg.hdr).fields:
        if(fieldInfo.count == 1):
            columnText = str(Messaging.get(msg, fieldInfo)) + ", "
            for bitInfo in fieldInfo.bitfieldInfo:
                columnText += str(Messaging.get(msg, bitInfo)) + ", "
        else:
            columnText = ""
            for i in range(0,fieldInfo.count):
                columnText += str(Messaging.get(msg, fieldInfo, i)) + ", "
        ret += columnText
    return ret

def escapeCommasInQuotedString(line):
    ret = ""
    quoteStarted = 0
    for c in line:
        if c == '"':
            quoteStarted = not quoteStarted
        elif c == ',':
            if quoteStarted:
                ret = ret + '\\'
        ret = ret + c
    return ret

def csvToMsg(lineOfText):
    if lineOfText == '':
        return None
    params = lineOfText.split(" ", 1)
    msgName = params[0]
    if len(params) == 1:
        params = []
    else:
        # escape commas that are inside quoted strings
        line = escapeCommasInQuotedString(params[1])
        # use CSV reader module
        params = list(csv.reader([line], quotechar='"', delimiter=',', quoting=csv.QUOTE_NONE, skipinitialspace=True, escapechar='\\'))[0]
        #print("params is " + str(params))
    if msgName in Messaging.MsgClassFromName:
        msgClass = Messaging.MsgClassFromName[msgName]
        msg = msgClass()
        terminateMsg = 0
        terminationLen = 0
        if msg.fields:
            try:
                paramNumber = 0
                for fieldInfo in msgClass.fields:
                    val = params[paramNumber].strip()
                    #print("val is [" + val + "]") 
                    if(fieldInfo.count == 1):
                        if val.endswith(";"):
                            terminateMsg = 1
                            val = val[:-1]
                            if val == "":
                                # terminate without this field
                                terminationLen = int(fieldInfo.get.offset)
                                break
                            # terminate after this field
                            terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size)
                        if len(fieldInfo.bitfieldInfo) == 0:
                            if fieldInfo.type == "string":
                                if val.startswith('"') and val.endswith('"'):
                                    val = val.strip('"')
                                if terminateMsg:
                                    terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size) * len(val)
                            Messaging.set(msg, fieldInfo, val)
                            paramNumber+=1
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                Messaging.set(msg, bitInfo, val)
                                paramNumber+=1
                                val = params[paramNumber]
                    else:
                        if val.startswith("0x") and len(val) > 2+fieldInfo.count*int(fieldInfo.get.size):
                            if val.endswith(";"):
                                terminateMsg = 1
                                val = val[:-1]
                                hexStr = val[2:].strip()
                                terminationLen = int(int(fieldInfo.get.offset) + len(hexStr)/2)
                            hexStr = val[2:].strip()
                            charsForOneElem = int(fieldInfo.get.size)*2
                            valArray = [hexStr[i:i+charsForOneElem] for i in range(0, len(hexStr), charsForOneElem)]
                            for i in range(0,len(valArray)):
                                Messaging.set(msg, fieldInfo, int(valArray[i], 16), i)
                            paramNumber+=1
                        else:
                            for i in range(0,fieldInfo.count):
                                if val.endswith(";"):
                                    terminateMsg = 1
                                    terminationLen = int(fieldInfo.get.offset) + int(fieldInfo.get.size)*(i+1)
                                    val = val[:-1]
                                Messaging.set(msg, fieldInfo, val, i)
                                if terminateMsg:
                                    break
                                paramNumber+=1
                                val = params[paramNumber]
                    if terminateMsg:
                        break
            except IndexError:
                # if index error occurs on accessing params, then stop processing params
                # because we've processed them all
                pass
        if terminateMsg:
            msg.hdr.SetDataLength(terminationLen)
        return msg
    else:
        #print("["+lineOfText+"] is NOT A MESSAGE NAME!")
        pass
    return None

def long_substr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for j in range(len(data[0])-1):
            if j > len(substr) and all(data[0][0:j] in x for x in data):
                substr = data[0][0:j]
    return substr

def paramHelp(field):
    ret = field.name
    if field.units:
        ret = ret + "(" + field.units + ")"
    if field.description:
        ret = ret + "# " + field.description
    return ret

def csvHelp(lineOfText):
    autoComplete = None
    help = ""
    params = lineOfText.split()
    if params:
        msgName = params[0]
    else:
        msgName = ''
    # if there's no params beyond first word, try to auto-complete a message name
    if len(params) <= 1 and not lineOfText.endswith(" "):
        # search for messages that match us
        matchingMsgNames = []
        truncated = False
        for aMsgName in sorted(Messaging.MsgClassFromName.keys()):
            if aMsgName.startswith(msgName):
                # truncate to first dot after match
                firstdot = aMsgName.find('.',len(msgName))
                if firstdot > 0:
                    aMsgName = aMsgName[0:firstdot+1]
                    truncated = True
                if not matchingMsgNames or aMsgName != matchingMsgNames[-1]:
                    matchingMsgNames.append(aMsgName)
        if len(matchingMsgNames) == 1:
            help = matchingMsgNames[0]
            autoComplete = matchingMsgNames[0]
            # if there's only one result and we don't match it exactly (because it's longer than us)
            # accept it by giving it as autoComplete with a space at end
            #if autoComplete != msgName:
            if not truncated:
                autoComplete = autoComplete + ' '
            return (autoComplete, help)
        else:
            help = '\n'.join(matchingMsgNames)
            autoComplete = long_substr(matchingMsgNames)
            #print("long_substr returned " + autoComplete)
            return (autoComplete, help)
            
    #print("param help")
    # if we didn't auto-complete a message name above, then show help on params
    paramstring = lineOfText.replace(msgName, "",1).strip()
    params = paramstring.split(',')
    if msgName in Messaging.MsgClassFromName:
        helpOnJustParam = len(paramstring)
        if not helpOnJustParam:
            help = msgName + " "
        msgClass = Messaging.MsgClassFromName[msgName]
        msg = msgClass()
        if msg.fields:
            try:
                paramNumber = 0
                for fieldInfo in msgClass.fields:
                    if(fieldInfo.count == 1):
                        if len(fieldInfo.bitfieldInfo) == 0:
                            if helpOnJustParam:
                                if paramNumber == len(params)-1:
                                    return (None, Messaging.paramHelp(fieldInfo))
                                paramNumber+=1
                            else:
                                help += fieldInfo.name + ", "
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                if helpOnJustParam:
                                    if paramNumber == len(params)-1:
                                        return (None, Messaging.paramHelp(bitInfo))
                                    paramNumber+=1
                                else:
                                    help += bitInfo.name + ", "
                    else:
                        if helpOnJustParam:
                            arrayList = []
                            for i in range(0,fieldInfo.count):
                                if helpOnJustParam and paramNumber == len(params)-1:
                                    return (None, Messaging.paramHelp(fieldInfo))
                                paramNumber+=1
                        else:
                            help += fieldInfo.name + "["+str(fieldInfo.count)+"], "
            except IndexError:
                # if index error occurs on accessing params, then stop processing params
                # because we've processed them all
                print("done at index " + str(paramNumber))
                pass
            if help.endswith(", "):
                help = help[:-2]
    else:
        return (None, "["+msgName+"] is not a message name!")
    return (autoComplete, help)
