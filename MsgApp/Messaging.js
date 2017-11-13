function toJSON(obj) {
    console.log("JSON for " + obj.MSG_NAME + ", ID=",+obj.MSG_ID+", "+obj.MSG_SIZE+" bytes")
    var jsonStr = '{"'+obj.MsgName()+'": ';
    jsonStr += JSON.stringify(obj.toObject());
    jsonStr += '}'
    return jsonStr;
}

function buf2hex(buffer) { // buffer is an ArrayBuffer
  return Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
}

var MessageDictionary = {};
    
var MessagingClient = function(name) {
    this.clientName = name
    var urlParams = new URLSearchParams(window.location.search);
    
    // use default localhost, or else address specified in URL
    websocketServer = "127.0.0.1";
    if(urlParams.has('ws'))
    {
        websocketServer = urlParams.get("ws")
    }

    // use default port, or else port specified in URL
    websocketPort = "5679";
    if(urlParams.has('port'))
    {
        websocketPort = urlParams.get("port")
    }
    
    // don't specify subprotocol, our Qt Websocket server doesn't support that
    this.webSocket = new WebSocket("ws://"+websocketServer+":" + websocketPort); //, "BMAP");
    this.webSocket.binaryType = 'arraybuffer';
    this.webSocket.onopen = this.onopen.bind(this);
    this.webSocket.onclose = this.onclose.bind(this);
    this.webSocket.onmessage = this.onmessage.bind(this);
}

MessagingClient.prototype.onopen = function (event) {
    cm = new Connect();
    cm.SetNameString(""+this.clientName);
    this.send(cm);

    // default values will make us receive all messages
    sm = new MaskedSubscription();
    this.send(sm);

    if(typeof this.onconnect === "function")
    {
        this.onconnect();
    }

};

MessagingClient.prototype.onclose = function(event) {
    console.log("Websocket closed");    
    if(typeof this.onconnect === "function")
    {
        this.onclose();
    }
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
        // construct a Unknown message
        //console.log("ERROR! Msg ID 0x" + id.toString(16) + " not defined!");
        msg = new UnknownMsg(event.data);
        this.onmsg(msg);
    }
};

MessagingClient.prototype.send = function (msg) {
    this.webSocket.send(msg.m_data.buffer);
};

MessagingClient.prototype.startlogging = function ()
{
    sl = new StartLog();
    sl.SetLogFileType("JSON");
    this.send(sl);
}

MessagingClient.prototype.stoplogging = function ()
{
        sl = new StopLog();
        this.send(sl);
}
