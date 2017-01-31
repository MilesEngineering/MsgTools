function toJSON(obj) {
    console.log("JSON for " + obj.MSG_NAME + ", ID=",+obj.MSG_ID+", "+obj.MSG_SIZE+" bytes")
    var jsonStr = '"'+obj.MSG_NAME+'": {\n';
    for (var property in obj.constructor.prototype) {
        if(typeof(obj[property]) == "function" && property.startsWith("Get"))
        {
            var fieldName = property.replace(/^Get/, '')
            var fieldValue = obj[property]();
            var line = '    "'+fieldName+'": ' + fieldValue;
            jsonStr += line+", \n";
        }
    }
    jsonStr = jsonStr.replace(/, \n$/g, '\n');
    jsonStr += '}\n';
    return jsonStr;
}

function buf2hex(buffer) { // buffer is an ArrayBuffer
  return Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
}

var MessageDictionary = {};
    
var MessagingClient = function() {
    this.webSocket = new WebSocket("ws://127.0.0.1:5679", "BMAP");
    this.webSocket.binaryType = 'arraybuffer';
    this.webSocket.onopen = this.onopen.bind(this);
    this.webSocket.onclose = this.onclose.bind(this);
    this.webSocket.onmessage = this.onmessage.bind(this);
}

MessagingClient.prototype.onopen = function (event) {
    cm = new Connect();
    // messy, need a way to set arrays of uint8s with type=ASCII as a string.
    // update javascript code generator plugin for this, and then we can do:
    //cm.SetName("javascript");
    // see how python does it for an example
    cm.SetName('j'.charCodeAt(0), 0);
    cm.SetName('a'.charCodeAt(0), 1);
    cm.SetName('v'.charCodeAt(0), 2);
    cm.SetName('a'.charCodeAt(0), 3);
    cm.SetName('s'.charCodeAt(0), 4);
    cm.SetName('c'.charCodeAt(0), 5);
    cm.SetName('r'.charCodeAt(0), 6);
    cm.SetName('i'.charCodeAt(0), 7);
    cm.SetName('p'.charCodeAt(0), 8);
    cm.SetName('t'.charCodeAt(0), 9);
    cm.SetName('\0'.charCodeAt(0), 10);
    this.webSocket.send(cm.m_data.buffer);

    // default values will make us receive all messages
    sm = new MaskedSubscription();
    this.webSocket.send(sm.m_data.buffer);
};

MessagingClient.prototype.onclose = function(event) {
    console.log("Websocket closed");
};

MessagingClient.prototype.onmessage = function (event) {
    var hdr = new NetworkHeader(event.data);
    var id = hdr.GetMessageID();
    var strId = String(id >>> 0)
    if(strId in MessageDictionary)
    {
        msgClass = MessageDictionary[strId];
        msg = new msgClass(event.data);
        if(typeof this.onmsg === "function")
        {
            this.onmsg(msg);
        }
    }
    else
    {
        console.log("ERROR! Msg ID " + id + " not defined!");
    }
};
