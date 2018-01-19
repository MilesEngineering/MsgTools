import msgtools.parser.parser as MsgParser
from msgtools.parser.MsgUtils import *

# https://www.html5rocks.com/en/tutorials/webgl/typed_arrays/
# https://github.com/kig/DataStream.js
# https://www.html5rocks.com/en/tutorials/websockets/basics/

def fieldType(field):
    fieldTypeDict = \
    {"uint64":"long", "uint32":"long","uint16": "int",   "uint8": "short",
     "int64":"long",   "int32":"int",  "int16": "short",  "int8": "char",
      "float64":"double", "float32":"float"}
    typeStr = str.lower(field["Type"])
    return field["Type"].capitalize()

def fnHdr(field):
    ret = "// %s %s, (%s to %s)" % (MsgParser.fieldDescription(field), MsgParser.fieldUnits(field), MsgParser.fieldMin(field), MsgParser.fieldMax(field))
    return ret

def typeForScaledInt(field):
    numBits = MsgParser.fieldNumBits(field)
    if numBits > 24:
        return "double"
    return "float"

def enumLookup(field):
    lookup  = "if(value in <MSGSHORTNAME>."+ str(field["Enum"])+")\n"
    lookup += "        value = <MSGSHORTNAME>."+ str(field["Enum"])+"[value];\n"
    lookup += "    "
    return lookup

def reverseEnumLookup(field):
    lookup = "if(!enumAsInt)\n"
    lookup += "    if(value in <MSGSHORTNAME>.Reverse"+ str(field["Enum"])+")\n"
    lookup += "        value = <MSGSHORTNAME>.Reverse" + str(field["Enum"]) + "[value];\n    "
    return lookup

def getFn(field, offset):
    loc = str(offset)
    param = ""
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += "idx"
    if "Enum" in field:
        if param != "":
            param += ", "
        param += "enumAsInt=false"
    access = "(this.m_data.get%s(%s))" % (fieldType(field), loc)
    access = getMath(access, field, "")
    cleanup = ""
    if "Enum" in field:
        cleanup = reverseEnumLookup(field)
    ret = '''\
%s
<MSGSHORTNAME>.prototype.Get%s = function(%s)
{
    var value = %s;
    %sreturn value;
};''' % (fnHdr(field), field["Name"], param, access, cleanup)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
<MSGSHORTNAME>.prototype.Get%sString = function()
{
    var value = '';
    for(i=0; i<%s && i<this.hdr.GetDataLength()-%s; i++)
    {
        nextChar = String.fromCharCode(this.Get%s(i));
        if(nextChar == '\\0')
            break;
        value += nextChar;
    }
    return value;
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), offset, field["Name"])
    return ret

def setFn(field, offset):
    valueString = setMath("value", field, "")
    lookup = ""
    if "Enum" in field:
        # find index that corresponds to string input param
        lookup = enumLookup(field)        
    param = "value"
    loc = str(offset)
    if MsgParser.fieldCount(field) > 1:
        loc += "+idx*" + str(MsgParser.fieldSize(field))
        param += ", idx"
    ret = '''\
%s
<MSGSHORTNAME>.prototype.Set%s = function(%s)
{
    %sthis.m_data.set%s(%s, %s);
};''' % (fnHdr(field), field["Name"], param, lookup, fieldType(field), loc, valueString)
    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        ret += '''
%s
<MSGSHORTNAME>.prototype.Set%sString = function(value)
{
    for(i=0; i<%s && i<value.length; i++)
    {
        this.Set%s(value[i].charCodeAt(0), i);
    }
};''' % (fnHdr(field), field["Name"], str(MsgParser.fieldCount(field)), field["Name"])
    return ret

def getBitsFn(field, bits, offset, bitOffset, numBits):
    access = "(this.Get%s() >> %s) & %s" % (field["Name"], str(bitOffset), MsgParser.Mask(numBits))
    access = getMath(access, bits, "")
    param = ""
    if "Enum" in bits:
        param += "enumAsInt=false"
    cleanup = ""
    if "Enum" in bits:
        cleanup = reverseEnumLookup(bits)
    ret = '''\
%s
<MSGSHORTNAME>.prototype.Get%s = function(%s)
{
    var value = %s;
    %sreturn value;
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), param, access, cleanup)
    return ret

def setBitsFn(field, bits, offset, bitOffset, numBits):
    valueString = setMath("value", bits, "")
    lookup = ""
    if "Enum" in bits:
        # find index that corresponds to string input param
        lookup = enumLookup(bits)
    ret = '''\
%s
<MSGSHORTNAME>.prototype.Set%s = function(value)
{
    %sthis.Set%s((this.Get%s() & ~(%s << %s)) | ((%s & %s) << %s));
};''' % (fnHdr(bits), MsgParser.BitfieldName(field, bits), lookup, field["Name"], field["Name"], MsgParser.Mask(numBits), str(bitOffset), valueString, MsgParser.Mask(numBits), str(bitOffset))
    return ret

def accessors(msg):
    gets = []
    sets = []
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            gets.append(getFn(field, offset))
            sets.append(setFn(field, offset))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    gets.append(getBitsFn(field, bits, offset, bitOffset, numBits))
                    sets.append(setBitsFn(field, bits, offset, bitOffset, numBits))
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return gets+sets

def initField(field):
    if "Default" in field:
        if MsgParser.fieldCount(field) > 1:
            ret = "for (i=0; i<" + str(MsgParser.fieldCount(field)) + "; i++)\n"
            ret += "    this.Set" + field["Name"] + "(" + str(field["Default"]) + ", i);" 
            return ret;
        else:
            return  "this.Set" + field["Name"] + "(" + str(field["Default"]) + ");"
    return ""

def initBitfield(field, bits):
    if "Default" in bits:
        return  "this.Set" + MsgParser.BitfieldName(field, bits) + "(" +str(bits["Default"]) + ");"
    return ""

def initCode(msg):
    ret = []
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInit = initField(field)
            if fieldInit:
                ret.append(fieldInit)
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    bits = initBitfield(field, bits)
                    if bits:
                        ret.append(bits)

    return ret

def enums(e):
    ret = ""
    for enum in e:
        # forward enum
        fwd = "<MSGSHORTNAME>." + enum["Name"]+" = {};\n"
        for option in enum["Options"]:
            fwd += "<MSGSHORTNAME>."+enum["Name"] + "[\"" + str(option["Name"]) + "\"] = "+str(option["Value"])+";\n"

        # Reverse enum
        back = "<MSGSHORTNAME>.Reverse" + enum["Name"]+" = {};\n"
        back += "for(key in <MSGSHORTNAME>."+enum["Name"]+") {\n"
        back += "    <MSGSHORTNAME>.Reverse" + enum["Name"] + "[<MSGSHORTNAME>."+enum["Name"]+"[key]" +"] = key;\n"
        back += "}\n"

        ret += fwd + back
    return ret

def reflectionInterfaceType(field):
    type = field["Type"]
    if "float" in type or "Offset" in field or "Scale" in field:
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitsReflectionInterfaceType(field):
    type = "int"
    if "Offset" in field or "Scale" in field:
        type = "float"
    elif MsgParser.fieldUnits(field) == "ASCII":
        type = "string"
    elif "Enum" in field:
        type = "enumeration"
    else:
        type = "int"
    return type

def bitfieldReflection(msg, field, bits):
    name = bits["Name"]
    ret = "{"+\
              'name:"'+name + '",'+\
              'type:"'+bitsReflectionInterfaceType(bits) + '",'+\
              'units:"'+MsgParser.fieldUnits(bits) + '",'+\
              'minVal:"'+str(MsgParser.fieldMin(bits)) + '",'+\
              'maxVal:"'+str(MsgParser.fieldMax(bits)) + '",'+\
              'description:"'+MsgParser.fieldDescription(bits) + '",'+\
              'get:"Get' + name + '",'+\
              'set:"Set' + name  + '", '
    if "Enum" in bits:
        ret += "enumLookup : [<MSGSHORTNAME>."+  bits["Enum"]+", " + "<MSGSHORTNAME>.Reverse" + bits["Enum"]+"]}"
    else:
        ret += "enumLookup : []}"
    return ret

def fieldReflection(msg, field):
    fieldFnName = field["Name"]
    fieldCount = MsgParser.fieldCount(field)
    if MsgParser.fieldCount(field) != 1 and MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
        fieldFnName = field["Name"]+"String"
        fieldCount = 1
    fieldInfo = "{"+\
                  'name:"'+field["Name"] + '",'+\
                  'type:"'+reflectionInterfaceType(field) + '",'+\
                  'units:"'+MsgParser.fieldUnits(field) + '",'+\
                  'minVal:"'+str(MsgParser.fieldMin(field)) + '",'+\
                  'maxVal:"'+str(MsgParser.fieldMax(field)) + '",'+\
                  'description:"'+MsgParser.fieldDescription(field) + '",'+\
                  'get:"Get' + fieldFnName + '",'+\
                  'set:"Set' + fieldFnName  + '",'+\
                  'count:'+str(fieldCount) + ', '
    if "Bitfields" in field:
        bitfieldInfo = []
        for bits in field["Bitfields"]:
            bitfieldInfo.append("    " + bitfieldReflection(msg, field, bits))
        fieldInfo += "bitfieldInfo : [\n" + ",\n".join(bitfieldInfo) + "], "
    else:
        fieldInfo += "bitfieldInfo : [], "
    if "Enum" in field:
        fieldInfo += "enumLookup : [<MSGSHORTNAME>." + field["Enum"]+", " + "<MSGSHORTNAME>.Reverse" + field["Enum"]+"]}"
    else:
        fieldInfo += "enumLookup : []}"
    return fieldInfo

def reflection(msg):
    fieldInfos = []
    if "Fields" in msg:
        for field in msg["Fields"]:
            fieldInfos.append(fieldReflection(msg, field))
    return ",\n".join(fieldInfos)

def genericInfo(field, type, offset):
    loc = str(offset)
    params  = '    static final int loc   = ' + loc + ';\n'
    params += '    static final '+type+' max   = ' + fieldMax(field) + ';\n'
    params += '    static final '+type+' min   = ' + fieldMin(field) + ';\n'
    params += '    static final String units = "' + str(MsgParser.fieldUnits(field)) + '"' + ';\n'
    params += '    static final int count = ' + str(MsgParser.fieldCount(field)) + ';\n'
    if "Default" in field:
        params += '    static final '+type+' defaultValue = ' + str(field["Default"]) + ";\n" 
    if "Scale" in field:
        params += '    static final int scale = ' + str(field["Scale"]) + ';\n'
    if "Offset" in field:
        params += '    static final int offset = ' + str(field["Offset"]) + ';\n'
    return params
    
def fieldInfo(field, offset):
    retType = fieldType(field)
    if "Offset" in field or "Scale" in field:
        retType = typeForScaledInt(field)

    params  = 'class ' + field["Name"] + 'FieldInfo {\n'
    params += genericInfo(field, retType, offset)
    params += '};\n'
    return params

def fieldBitsInfo(field, bits, offset, bitOffset, numBits):
    retType = fieldType(field)
    if "Offset" in bits or "Scale" in bits:
        retType = typeForScaledInt(bits)

    params  = 'class ' + bits["Name"] + 'FieldInfo {\n'
    params += genericInfo(bits, retType, offset)
    params += '    static final int bitOffset = ' + str(bitOffset) + ';\n'
    params += '    static final int numBits   = ' + str(numBits) + ';\n'
    params += '};\n'
    return params

def fieldInfos(msg):
    ret = []
    
    offset = 0
    if "Fields" in msg:
        for field in msg["Fields"]:
            ret.append(fieldInfo(field, offset))
            bitOffset = 0
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    numBits = bits["NumBits"]
                    ret.append(fieldBitsInfo(field, bits, offset, bitOffset, numBits))
                    bitOffset += numBits
            offset += MsgParser.fieldSize(field) * MsgParser.fieldCount(field)

    return "\n".join(ret)
    
def declarations(msg):
    return []

def getMsgID(msg):
    return baseGetMsgID("this.", "", 0, 1, msg)
    
def setMsgID(msg):
    return baseSetMsgID("this.", "", 0, 1, msg)

def structUnpacking(msg):
    ret = []

    if "Fields" in msg:    
        for field in msg["Fields"]:
            if "Bitfields" in field:
                for bits in field["Bitfields"]:
                    ret.append('try { ret["'+bits["Name"] + '"] = this.Get' + bits["Name"] + "(); } catch (err) {}")
            else:
                if MsgParser.fieldCount(field) == 1:
                    ret.append('try { ret["'+field["Name"] + '"] = this.Get' + field["Name"] + "(); } catch (err) {}")
                else:
                    if MsgParser.fieldUnits(field) == "ASCII" and (field["Type"] == "uint8" or field["Type"] == "int8"):
                        ret.append('try { ret["'+field["Name"] + '"] = this.Get' + field["Name"] + "String(); } catch (err) {}")
                    else:
                        ret.append('try { ret["'+field["Name"] + '"] = []; } catch (err) {}')
                        ret.append('try { ')
                        ret.append("    for(i=0; i<"+str(MsgParser.fieldCount(field))+"; i++)")
                        ret.append('        ret["'+field["Name"] + '"][i] = this.Get' + field["Name"] + "(i);")
                        ret.append('} catch (err) {}')
            
    return "\n".join(ret)
