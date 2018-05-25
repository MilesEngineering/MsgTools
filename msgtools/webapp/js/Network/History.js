/*
    ./js/Network/History.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//Network/History.yaml
        Template = Template.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
//import { NetworkHeader } from '../headers/NetworkHeader.js'
//import MessageDictionary from '../MessageDictionary.js'

var GetData = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE+GetData.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
        this.hdr.SetMessageID(GetData.prototype.MSG_ID);
        this.hdr.SetDataLength(buffer.byteLength - NetworkHeader.prototype.MSG_SIZE);
        //this.InitializeTime();
        this.Init();
    }
    else
    {
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
    }
};

// This is for 0.28.42/Messaging.js compatibility
if (typeof(MessageDictionary)!=='undefined' && MessageDictionary != null)
    // add our class to the dictionary
    MessageDictionary[4294967051] = GetData

// This is for 0.29.42/msgtools.js compatibility
if (typeof msgtools === 'object')
    msgtools.registerMessage(4294967051,GetData)

// how to make constants?
GetData.prototype.MSG_ID = 4294967051;
GetData.prototype.MSG_SIZE = 144;
GetData.prototype.MSG_NAME = "s/Network.GetData";

GetData.prototype.MsgName = function(){
    return "s/Network.GetData";
}

GetData.prototype.Init = function(){
};


// http://stackoverflow.com/a/130572
//  , (DBL_MIN to DBL_MAX)
GetData.prototype.GetStartTime = function()
{
    var value = (this.m_data.getFloat64(0));
    return value;
};
//  , (DBL_MIN to DBL_MAX)
GetData.prototype.GetEndTime = function()
{
    var value = (this.m_data.getFloat64(8));
    return value;
};
// time period to average over , (DBL_MIN to DBL_MAX)
GetData.prototype.GetAveragingTime = function()
{
    var value = (this.m_data.getFloat64(16));
    return value;
};
// msgname.fieldname,tagquery ASCII, (0 to 255)
GetData.prototype.GetQuery = function(idx)
{
    var value = (this.m_data.getUint8(24+idx*1));
    return value;
};
// msgname.fieldname,tagquery ASCII, (0 to 255)
GetData.prototype.GetQueryString = function()
{
    var value = '';
    for(i=0; i<120 && i<this.hdr.GetDataLength()-24; i++)
    {
        nextChar = String.fromCharCode(this.GetQuery(i));
        if(nextChar == '\0')
            break;
        value += nextChar;
    }
    return value;
};
//  , (DBL_MIN to DBL_MAX)
GetData.prototype.SetStartTime = function(value)
{
    this.m_data.setFloat64(0, value);
};
//  , (DBL_MIN to DBL_MAX)
GetData.prototype.SetEndTime = function(value)
{
    this.m_data.setFloat64(8, value);
};
// time period to average over , (DBL_MIN to DBL_MAX)
GetData.prototype.SetAveragingTime = function(value)
{
    this.m_data.setFloat64(16, value);
};
// msgname.fieldname,tagquery ASCII, (0 to 255)
GetData.prototype.SetQuery = function(value, idx)
{
    this.m_data.setUint8(24+idx*1, value);
};
// msgname.fieldname,tagquery ASCII, (0 to 255)
GetData.prototype.SetQueryString = function(value)
{
    for(i=0; i<120 && i<value.length; i++)
    {
        this.SetQuery(value[i].charCodeAt(0), i);
    }
};

// Convert to a javascript object
GetData.prototype.toObject = function(){
    ret = {};
    try { ret["StartTime"] = this.GetStartTime(); } catch (err) {}
    try { ret["EndTime"] = this.GetEndTime(); } catch (err) {}
    try { ret["AveragingTime"] = this.GetAveragingTime(); } catch (err) {}
    try { ret["Query"] = this.GetQueryString(); } catch (err) {}
    return ret;
}

// Reflection information
GetData.prototype.fields = [
    {name:"StartTime",type:"float",units:"",minVal:"DBL_MIN",maxVal:"DBL_MAX",description:"",get:"GetStartTime",set:"SetStartTime",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"EndTime",type:"float",units:"",minVal:"DBL_MIN",maxVal:"DBL_MAX",description:"",get:"GetEndTime",set:"SetEndTime",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"AveragingTime",type:"float",units:"",minVal:"DBL_MIN",maxVal:"DBL_MAX",description:"time period to average over",get:"GetAveragingTime",set:"SetAveragingTime",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"Query",type:"string",units:"ASCII",minVal:"0",maxVal:"255",description:"msgname.fieldname,tagquery",get:"GetQueryString",set:"SetQueryString",count:1, bitfieldInfo : [], enumLookup : []}
]

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.GetData = GetData;
/*
    ./js/Network/History.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//Network/History.yaml
        Template = Template.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
//import { NetworkHeader } from '../headers/NetworkHeader.js'
//import MessageDictionary from '../MessageDictionary.js'

var QueryResult = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE+QueryResult.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
        this.hdr.SetMessageID(QueryResult.prototype.MSG_ID);
        this.hdr.SetDataLength(buffer.byteLength - NetworkHeader.prototype.MSG_SIZE);
        //this.InitializeTime();
        this.Init();
    }
    else
    {
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
    }
};

// This is for 0.28.42/Messaging.js compatibility
if (typeof(MessageDictionary)!=='undefined' && MessageDictionary != null)
    // add our class to the dictionary
    MessageDictionary[4294967052] = QueryResult

// This is for 0.29.42/msgtools.js compatibility
if (typeof msgtools === 'object')
    msgtools.registerMessage(4294967052,QueryResult)

// how to make constants?
QueryResult.prototype.MSG_ID = 4294967052;
QueryResult.prototype.MSG_SIZE = 124;
QueryResult.prototype.MSG_NAME = "s/Network.QueryResult";

QueryResult.prototype.MsgName = function(){
    return "s/Network.QueryResult";
}

QueryResult.prototype.Init = function(){
};


// http://stackoverflow.com/a/130572
// Unique value in all History.Data messages for this QueryResult , (0 to 65535)
QueryResult.prototype.GetCookie = function()
{
    var value = (this.m_data.getUint16(0));
    return value;
};
// Number of History.Data messages that will be returned , (0 to 65535)
QueryResult.prototype.GetResultCount = function()
{
    var value = (this.m_data.getUint16(2));
    return value;
};
// Echo of the requested Query ASCII, (0 to 255)
QueryResult.prototype.GetQuery = function(idx)
{
    var value = (this.m_data.getUint8(4+idx*1));
    return value;
};
// Echo of the requested Query ASCII, (0 to 255)
QueryResult.prototype.GetQueryString = function()
{
    var value = '';
    for(i=0; i<120 && i<this.hdr.GetDataLength()-4; i++)
    {
        nextChar = String.fromCharCode(this.GetQuery(i));
        if(nextChar == '\0')
            break;
        value += nextChar;
    }
    return value;
};
// Unique value in all History.Data messages for this QueryResult , (0 to 65535)
QueryResult.prototype.SetCookie = function(value)
{
    this.m_data.setUint16(0, value);
};
// Number of History.Data messages that will be returned , (0 to 65535)
QueryResult.prototype.SetResultCount = function(value)
{
    this.m_data.setUint16(2, value);
};
// Echo of the requested Query ASCII, (0 to 255)
QueryResult.prototype.SetQuery = function(value, idx)
{
    this.m_data.setUint8(4+idx*1, value);
};
// Echo of the requested Query ASCII, (0 to 255)
QueryResult.prototype.SetQueryString = function(value)
{
    for(i=0; i<120 && i<value.length; i++)
    {
        this.SetQuery(value[i].charCodeAt(0), i);
    }
};

// Convert to a javascript object
QueryResult.prototype.toObject = function(){
    ret = {};
    try { ret["Cookie"] = this.GetCookie(); } catch (err) {}
    try { ret["ResultCount"] = this.GetResultCount(); } catch (err) {}
    try { ret["Query"] = this.GetQueryString(); } catch (err) {}
    return ret;
}

// Reflection information
QueryResult.prototype.fields = [
    {name:"Cookie",type:"int",units:"",minVal:"0",maxVal:"65535",description:"Unique value in all History.Data messages for this QueryResult",get:"GetCookie",set:"SetCookie",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"ResultCount",type:"int",units:"",minVal:"0",maxVal:"65535",description:"Number of History.Data messages that will be returned",get:"GetResultCount",set:"SetResultCount",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"Query",type:"string",units:"ASCII",minVal:"0",maxVal:"255",description:"Echo of the requested Query",get:"GetQueryString",set:"SetQueryString",count:1, bitfieldInfo : [], enumLookup : []}
]

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.QueryResult = QueryResult;
/*
    ./js/Network/History.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//Network/History.yaml
        Template = Template.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
//import { NetworkHeader } from '../headers/NetworkHeader.js'
//import MessageDictionary from '../MessageDictionary.js'

var Data = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE+Data.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
        this.hdr.SetMessageID(Data.prototype.MSG_ID);
        this.hdr.SetDataLength(buffer.byteLength - NetworkHeader.prototype.MSG_SIZE);
        //this.InitializeTime();
        this.Init();
    }
    else
    {
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
    }
};

// This is for 0.28.42/Messaging.js compatibility
if (typeof(MessageDictionary)!=='undefined' && MessageDictionary != null)
    // add our class to the dictionary
    MessageDictionary[4294967053] = Data

// This is for 0.29.42/msgtools.js compatibility
if (typeof msgtools === 'object')
    msgtools.registerMessage(4294967053,Data)

// how to make constants?
Data.prototype.MSG_ID = 4294967053;
Data.prototype.MSG_SIZE = 516;
Data.prototype.MSG_NAME = "s/Network.Data";

Data.prototype.MsgName = function(){
    return "s/Network.Data";
}

Data.prototype.Init = function(){
};


// http://stackoverflow.com/a/130572
// Unique value that matches our QueryResult , (0 to 65535)
Data.prototype.GetCookie = function()
{
    var value = (this.m_data.getUint16(0));
    return value;
};
// Sequence number of our data message , (0 to 65535)
Data.prototype.GetResultNumber = function()
{
    var value = (this.m_data.getUint16(2));
    return value;
};
// Alternating timestamps and values , (DBL_MIN to DBL_MAX)
Data.prototype.GetData = function(idx)
{
    var value = (this.m_data.getFloat64(4+idx*8));
    return value;
};
// Unique value that matches our QueryResult , (0 to 65535)
Data.prototype.SetCookie = function(value)
{
    this.m_data.setUint16(0, value);
};
// Sequence number of our data message , (0 to 65535)
Data.prototype.SetResultNumber = function(value)
{
    this.m_data.setUint16(2, value);
};
// Alternating timestamps and values , (DBL_MIN to DBL_MAX)
Data.prototype.SetData = function(value, idx)
{
    this.m_data.setFloat64(4+idx*8, value);
};

// Convert to a javascript object
Data.prototype.toObject = function(){
    ret = {};
    try { ret["Cookie"] = this.GetCookie(); } catch (err) {}
    try { ret["ResultNumber"] = this.GetResultNumber(); } catch (err) {}
    try { ret["Data"] = []; } catch (err) {}
    try { 
        for(i=0; i<64; i++)
            ret["Data"][i] = this.GetData(i);
    } catch (err) {}
    return ret;
}

// Reflection information
Data.prototype.fields = [
    {name:"Cookie",type:"int",units:"",minVal:"0",maxVal:"65535",description:"Unique value that matches our QueryResult",get:"GetCookie",set:"SetCookie",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"ResultNumber",type:"int",units:"",minVal:"0",maxVal:"65535",description:"Sequence number of our data message",get:"GetResultNumber",set:"SetResultNumber",count:1, bitfieldInfo : [], enumLookup : []},
    {name:"Data",type:"float",units:"",minVal:"DBL_MIN",maxVal:"DBL_MAX",description:"Alternating timestamps and values",get:"GetData",set:"SetData",count:64, bitfieldInfo : [], enumLookup : []}
]

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.Data = Data;
