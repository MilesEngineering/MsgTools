from .messaging import Messaging

# for reading CSV
import csv

def toCsv(msg, nameColumn=True, timeColumn=False):
    def add_param(v):
        if v.strip() == '':
            v = '"%s"' % v
        if ',' in v and not((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
            v = '"%s"' % v
        return v + ", "
    ret = ""
    if timeColumn:
        t = msg.hdr.GetTime()
        if Messaging.findFieldInfo(msg.hdr.fields, "Time").units == "ms":
            t = t / 1000
        ret += str(t) + ', '
    if nameColumn:
        ret += msg.MsgName() + ", "
    for fieldInfo in Messaging.MsgClass(msg.hdr).fields:
        if(fieldInfo.count == 1):
            if not fieldInfo.exists(msg):
                break
            if len(fieldInfo.bitfieldInfo) == 0:
                columnText = add_param(str(Messaging.get(msg, fieldInfo)))
            else:
                columnText = ""
                for bitInfo in fieldInfo.bitfieldInfo:
                    columnText += add_param(str(Messaging.get(msg, bitInfo)))
        else:
            columnText = ""
            for i in range(0,fieldInfo.count):
                if not fieldInfo.exists(msg, i):
                    break
                columnText += add_param(str(Messaging.get(msg, fieldInfo, i)))
        ret += columnText
    # drop last two chars (', ') off end
    return ret[:-2]

def csvHeader(msg, nameColumn=True, timeColumn=False):
    tableHeader = ''
    if timeColumn:
        timeUnits = Messaging.findFieldInfo(msg.hdr.fields, "Time").units
        if timeUnits == "ms":
            timeUnits = "s"
        if timeUnits:
            timeUnits = " (%s)" % timeUnits
        tableHeader = "Time"+timeUnits+", "
    if nameColumn:
        tableHeader += msg.MsgName() + ", "
    for fieldInfo in type(msg).fields:
        if len(fieldInfo.bitfieldInfo) == 0:
            tableHeader += fieldInfo.name + ", "
        else:
            for bitInfo in fieldInfo.bitfieldInfo:
                tableHeader += bitInfo.name + ", "
    # drop last two chars (', ') off end
    return tableHeader[:-2]

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

def msgNameAndParams(lineOfText):
    # check for message name followed by space
    params = lineOfText.split(" ", 1)
    msgName = params[0]
    if msgName in Messaging.MsgClassFromName:
        pass
    else:
        params = lineOfText.split(",", 1)
        msgName = params[0].strip()
    if len(params) == 1:
        params = []
    else:
        # escape commas that are inside quoted strings
        line = escapeCommasInQuotedString(params[1])
        # use CSV reader module
        params = list(csv.reader([line], quotechar='"', delimiter=',', quoting=csv.QUOTE_NONE, skipinitialspace=True, escapechar='\\'))[0]
        #print("params is " + str(params))
    return msgName, params
    
def csvToMsg(lineOfText):
    if lineOfText == '':
        return None
    msgName, params = msgNameAndParams(lineOfText)
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
                        if len(fieldInfo.bitfieldInfo) == 0:
                            if val.endswith(";"):
                                terminateMsg = 1
                                val = val[:-1]
                                if val == "":
                                    # terminate without this field
                                    terminationLen = fieldInfo.offset
                                    break
                                # terminate after this field
                                #TODO Broken for arrays-of-structs acting like parallel arrays!
                                terminationLen = fieldInfo.end_location()
                            if fieldInfo.type == "string":
                                if val.startswith('"') and val.endswith('"'):
                                    val = val.strip('"')
                                if terminateMsg:
                                    #TODO Broken for arrays-of-structs acting like parallel arrays!
                                    terminationLen = fieldInfo.end_location(len(val)-1)
                            Messaging.set(msg, fieldInfo, val)
                            paramNumber+=1
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                if val.endswith(";"):
                                    terminateMsg = 1
                                    val = val[:-1]
                                    # terminate without anything after our parent field
                                    terminationLen = fieldInfo.end_location()
                                    if val == "":
                                        break
                                Messaging.set(msg, bitInfo, val)
                                paramNumber+=1
                                val = params[paramNumber]
                                if terminateMsg:
                                    break
                    else:
                        if val.startswith("0x") and len(val) > 2+2*fieldInfo.size:
                            if val.endswith(";"):
                                terminateMsg = 1
                                val = val[:-1]
                                hexStr = val[2:].strip()
                                #TODO Broken for arrays-of-structs acting like parallel arrays!
                                terminationLen = int(fieldInfo.offset + len(hexStr)/2)
                            hexStr = val[2:].strip()
                            charsForOneElem = fieldInfo.size*2
                            valArray = [hexStr[i:i+charsForOneElem] for i in range(0, len(hexStr), charsForOneElem)]
                            for i in range(0,len(valArray)):
                                Messaging.set(msg, fieldInfo, int(valArray[i], 16), i)
                            paramNumber+=1
                        else:
                            for i in range(0,fieldInfo.count):
                                if val.endswith(";"):
                                    terminateMsg = 1
                                    #TODO Broken for arrays-of-structs acting like parallel arrays!
                                    terminationLen = fieldInfo.end_location(i)
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

def long_substr(string_array):
    if len(string_array) == 0:
        return ''
    if len(string_array) == 1:
        return string_array[0]
    if len(string_array[0]) == 0:
        return string_array[0]
    substr = ''
    # iterate over chars in first string
    for c in range(len(string_array[0])):
        # check if it matches all other strings
        for s in range(1,len(string_array)):
            if len(string_array[s]) <= c or string_array[0][c] != string_array[s][c]:
                return substr
        substr += string_array[0][c]
    return substr

def paramHelp(field):
    ret = field.name
    if field.units:
        ret = ret + "(" + field.units + ")"
    if field.description:
        ret = ret + "# " + field.description
    return ret

def csvHelp(lineOfText, verbose=False):
    autoComplete = None
    help = ""
    msgName, params = msgNameAndParams(lineOfText)
    # if there's no params beyond first word, try to auto-complete a message name
    if len(params) == 0 and not lineOfText.endswith(" ") and not lineOfText.endswith(","):
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
            # accept it by giving it as autoComplete with a comma at end
            #if autoComplete != msgName:
            if not truncated:
                autoComplete = autoComplete + ','
            return (autoComplete, help)
        else:
            help = '\n'.join(matchingMsgNames)
            autoComplete = long_substr(matchingMsgNames)
            #print("long_substr returned " + autoComplete)
            return (autoComplete, help)
            
    if msgName in Messaging.MsgClassFromName:
        msgClass = Messaging.MsgClassFromName[msgName]
        msg = msgClass()
        helpOnJustParam = len(params)>1 or (len(params) == 1 and params[0] != '')
        if not helpOnJustParam:
            help = msgName
            if verbose:
                help += ": \n"# + msg.msgDescription
            else:
                help += ", "
        if msg.fields:
            try:
                paramNumber = 0
                for fieldInfo in msgClass.fields:
                    if(fieldInfo.count == 1):
                        if len(fieldInfo.bitfieldInfo) == 0:
                            if helpOnJustParam:
                                if paramNumber == len(params):
                                    return (None, paramHelp(fieldInfo))
                                paramNumber+=1
                            else:
                                help += fieldInfo.name
                                if verbose:
                                    help += "(%s): %s\n" % (fieldInfo.units, fieldInfo.description)
                                else:
                                    help += ", "
                        else:
                            for bitInfo in fieldInfo.bitfieldInfo:
                                if helpOnJustParam:
                                    if paramNumber == len(params):
                                        return (None, paramHelp(bitInfo))
                                    paramNumber+=1
                                else:
                                    help += bitInfo.name
                                    if verbose:
                                        help += "(%s): %s\n" % (bitInfo.units, bitInfo.description)
                                    else:
                                        help += ", "
                    else:
                        if helpOnJustParam:
                            arrayList = []
                            for i in range(0,fieldInfo.count):
                                if helpOnJustParam and paramNumber == len(params):
                                    return (None, paramHelp(fieldInfo))
                                paramNumber+=1
                        else:
                            help += fieldInfo.name + "["+str(fieldInfo.count)+"]"
                            if verbose:
                                help += "(%s): %s\n" % (fieldInfo.units, fieldInfo.description)
                            else:
                                help += ", "
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
