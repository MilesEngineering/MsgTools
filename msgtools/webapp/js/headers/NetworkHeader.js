/*
    ./js/headers/NetworkHeader.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//headers/NetworkHeader.yaml
        Template = HeaderTemplate.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
var NetworkHeader = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer);
        this.Init();
    }
    else
    {
        this.m_data = new DataView(buffer);
    }
};

// how to make constants?
NetworkHeader.prototype.MSG_SIZE = 16;
NetworkHeader.prototype.MSG_NAME = "s/headers.NetworkHeader";

NetworkHeader.prototype.Init = function(){
    this.SetSource(0);
    this.SetDestination(0);
    this.SetID(0);
    this.SetPriority(0);
    this.SetDataLength(0);
    this.SetTime(0);
};


// http://stackoverflow.com/a/130572
//  , (0 to 65535)
NetworkHeader.prototype.GetSource = function()
{
    var value = (this.m_data.getUint16(0));
    return value;
};
//  , (0 to 65535)
NetworkHeader.prototype.GetDestination = function()
{
    var value = (this.m_data.getUint16(2));
    return value;
};
//  , (0 to 4294967295)
NetworkHeader.prototype.GetID = function()
{
    var value = (this.m_data.getUint32(4));
    return value;
};
// To hold bitfields , (0 to 4294967295)
NetworkHeader.prototype.GetPackedField = function()
{
    var value = (this.m_data.getUint32(8));
    return value;
};
//  , (0 to 255)
NetworkHeader.prototype.GetPriority = function()
{
    var value = (this.GetPackedField() >> 0) & 0xff;
    return value;
};
//  , (0 to 16777215)
NetworkHeader.prototype.GetDataLength = function()
{
    var value = (this.GetPackedField() >> 8) & 0xffffff;
    return value;
};
// Rolling millisecond counter. , (0 to 4294967295)
NetworkHeader.prototype.GetTime = function()
{
    var value = (this.m_data.getUint32(12));
    return value;
};
//  , (0 to 65535)
NetworkHeader.prototype.SetSource = function(value)
{
    this.m_data.setUint16(0, value);
};
//  , (0 to 65535)
NetworkHeader.prototype.SetDestination = function(value)
{
    this.m_data.setUint16(2, value);
};
//  , (0 to 4294967295)
NetworkHeader.prototype.SetID = function(value)
{
    this.m_data.setUint32(4, value);
};
// To hold bitfields , (0 to 4294967295)
NetworkHeader.prototype.SetPackedField = function(value)
{
    this.m_data.setUint32(8, value);
};
//  , (0 to 255)
NetworkHeader.prototype.SetPriority = function(value)
{
    this.SetPackedField((this.GetPackedField() & ~(0xff << 0)) | ((value & 0xff) << 0));
};
//  , (0 to 16777215)
NetworkHeader.prototype.SetDataLength = function(value)
{
    this.SetPackedField((this.GetPackedField() & ~(0xffffff << 8)) | ((value & 0xffffff) << 8));
};
// Rolling millisecond counter. , (0 to 4294967295)
NetworkHeader.prototype.SetTime = function(value)
{
    this.m_data.setUint32(12, value);
};
NetworkHeader.prototype.SetMessageID = function(id){
    this.SetID(id & 0xffffffff);
};
NetworkHeader.prototype.GetMessageID = function(){
    return this.GetID();
};

// Convert to a javascript object
NetworkHeader.prototype.toObject = function(){
    ret = {};
    try { ret["Source"] = this.GetSource(); } catch (err) {}
    try { ret["Destination"] = this.GetDestination(); } catch (err) {}
    try { ret["ID"] = this.GetID(); } catch (err) {}
    try { ret["Priority"] = this.GetPriority(); } catch (err) {}
    try { ret["DataLength"] = this.GetDataLength(); } catch (err) {}
    try { ret["Time"] = this.GetTime(); } catch (err) {}
    return ret;
}

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.NetworkHeader = NetworkHeader;
