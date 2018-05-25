/*
    ./js/Network/StopLog.js
    Created 25/05/2018 at 10:38:31 from:
        Messages = msgtools/parser/test/messages//Network/StopLog.yaml
        Template = Template.js
        Language = javascript

                     AUTOGENERATED FILE, DO NOT EDIT

*/
//import { NetworkHeader } from '../headers/NetworkHeader.js'
//import MessageDictionary from '../MessageDictionary.js'

var StopLog = function(buffer) {
    // have baseclass construct the buffer?
    //Message.call(this, MSG_SIZE);
        
    if (buffer==undefined)
    {
        buffer = new ArrayBuffer(NetworkHeader.prototype.MSG_SIZE+StopLog.prototype.MSG_SIZE);
        this.m_data = new DataView(buffer, NetworkHeader.prototype.MSG_SIZE);
        this.hdr = new NetworkHeader(buffer);
        this.hdr.SetMessageID(StopLog.prototype.MSG_ID);
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
    MessageDictionary[4294967046] = StopLog

// This is for 0.29.42/msgtools.js compatibility
if (typeof msgtools === 'object')
    msgtools.registerMessage(4294967046,StopLog)

// how to make constants?
StopLog.prototype.MSG_ID = 4294967046;
StopLog.prototype.MSG_SIZE = 0;
StopLog.prototype.MSG_NAME = "s/Network.StopLog";

StopLog.prototype.MsgName = function(){
    return "s/Network.StopLog";
}

StopLog.prototype.Init = function(){
};


// http://stackoverflow.com/a/130572

// Convert to a javascript object
StopLog.prototype.toObject = function(){
    ret = {};
    return ret;
}

// Reflection information
StopLog.prototype.fields = [
]

// for react-native and node.js, we should set module.exports so our class can be accessed externally
if(typeof module != 'undefined' && typeof module.exports != 'undefined')
    module.exports.StopLog = StopLog;
