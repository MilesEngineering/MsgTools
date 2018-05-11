/*
    This allows reflection to inspect a "unknown" message
*/
var UnknownMsg = function(buffer) {
    this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
    this.hdr = new NetworkHeader(buffer);
};

UnknownMsg.prototype.MsgName = function(){
    return "Unknown0x" + this.hdr.GetMessageID().toString(16);
}

// The string to display. ASCII, (0 to 255)
UnknownMsg.prototype.GetBuffer = function(idx)
{
    return this.m_data.getUint8(idx, false);
};
// The string to display. ASCII, (0 to 255)
UnknownMsg.prototype.GetBufferString = function()
{
    var value = '0x';
    for(i=0; i<this.m_data.byteLength ; i++)
    {
        value += ' ' + this.GetBuffer(i).toString(16);
    }
    return value;
};
// The string to display. ASCII, (0 to 255)
UnknownMsg.prototype.SetBuffer = function(value, idx)
{
    this.m_data.setUint8(idx, value, false);
};
// The string to display. ASCII, (0 to 255)
UnknownMsg.prototype.SetBufferString = function(value)
{
    value.removeStart('0x');
    value.split(' ');
    for(i=0; i<this.m_data.byteLength && i<value.length; i++)
    {
        this.SetBuffer(parseInt(value[i], 16), i);
    }
};

// Convert to a javascript object
UnknownMsg.prototype.toObject = function(){
    ret = {};
    ret["rawData"] = this.GetBufferString();
    return ret;
}
