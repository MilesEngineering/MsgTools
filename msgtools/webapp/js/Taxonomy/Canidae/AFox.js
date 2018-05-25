/*
    ./js/Taxonomy/Canidae/AFox.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//Taxonomy/Canidae/AFox.yaml
        Template = Template.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
//import { NetworkHeader } from '../headers/NetworkHeader.js'
//import MessageDictionary from '../MessageDictionary.js'

var AFox = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE+AFox.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
        this.hdr.SetMessageID(AFox.prototype.MSG_ID);
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
    MessageDictionary[16908289] = AFox

// This is for 0.29.42/msgtools.js compatibility
if (typeof msgtools === 'object')
    msgtools.registerMessage(16908289,AFox)

// how to make constants?
AFox.prototype.MSG_ID = 16908289;
AFox.prototype.MSG_SIZE = 17;
AFox.prototype.MSG_NAME = "s/Taxonomy/Canidae.AFox";

AFox.prototype.MsgName = function(){
    return "s/Taxonomy/Canidae.AFox";
}

AFox.prototype.Init = function(){
};


// http://stackoverflow.com/a/130572
AFox.Foods = {};
AFox.Foods["Steak"] = 1;
AFox.Foods["Bacon"] = 2;
AFox.ReverseFoods = {};
for(key in AFox.Foods) {
    AFox.ReverseFoods[AFox.Foods[key]] = key;
}
AFox.IDs = {};
AFox.IDs["Family"] = 1;
AFox.IDs["Genus"] = 2;
AFox.IDs["Species"] = 1;
AFox.ReverseIDs = {};
for(key in AFox.IDs) {
    AFox.ReverseIDs[AFox.IDs[key]] = key;
}

//  , (-128 to 127)
AFox.prototype.GetFavoriteFood = function(enumAsInt=false)
{
    var value = (this.m_data.getInt8(0));
    if(!enumAsInt)
    if(value in AFox.ReverseFoods)
        value = AFox.ReverseFoods[value];
    return value;
};
//  ASCII, (0 to 255)
AFox.prototype.GetName = function(idx)
{
    var value = (this.m_data.getUint8(1+idx*1));
    return value;
};
//  ASCII, (0 to 255)
AFox.prototype.GetNameString = function()
{
    var value = '';
    for(i=0; i<16 && i<this.hdr.GetDataLength()-1; i++)
    {
        nextChar = String.fromCharCode(this.GetName(i));
        if(nextChar == '\0')
            break;
        value += nextChar;
    }
    return value;
};
//  , (-128 to 127)
AFox.prototype.SetFavoriteFood = function(value)
{
    if(value in AFox.Foods)
        value = AFox.Foods[value];
    this.m_data.setInt8(0, value);
};
//  ASCII, (0 to 255)
AFox.prototype.SetName = function(value, idx)
{
    this.m_data.setUint8(1+idx*1, value);
};
//  ASCII, (0 to 255)
AFox.prototype.SetNameString = function(value)
{
    for(i=0; i<16 && i<value.length; i++)
    {
        this.SetName(value[i].charCodeAt(0), i);
    }
};

// Convert to a javascript object
AFox.prototype.toObject = function(){
    ret = {};
    try { ret["FavoriteFood"] = this.GetFavoriteFood(); } catch (err) {}
    try { ret["Name"] = this.GetNameString(); } catch (err) {}
    return ret;
}

// Reflection information
AFox.prototype.fields = [
    {name:"FavoriteFood",type:"enumeration",units:"",minVal:"-128",maxVal:"127",description:"",get:"GetFavoriteFood",set:"SetFavoriteFood",count:1, bitfieldInfo : [], enumLookup : [AFox.Foods, AFox.ReverseFoods]},
    {name:"Name",type:"string",units:"ASCII",minVal:"0",maxVal:"255",description:"",get:"GetNameString",set:"SetNameString",count:1, bitfieldInfo : [], enumLookup : []}
]

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.AFox = AFox;
