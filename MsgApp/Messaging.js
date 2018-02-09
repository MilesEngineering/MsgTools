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

function getWebsocketURLParams() {
    var url = new URL(window.location)
    var ws = "127.0.0.1"
    var port = 5679
    if (url.searchParams.has('ws'))
        ws = url.searchParams.get('ws')
    if (url.searchParams.has('port'))
        port = url.searchParams.get('port')

    return {websocketServer: ws, websocketPort:port}    
}

var MessageDictionary = {};
    
var MessagingClient = function(name, websocketServer="127.0.0.1", websocketPort=5679) {
    this.clientName = name
    this.webSocket = null
    
    this.connect(websocketServer, websocketPort)   
}

MessagingClient.prototype.connect = function(server, port) {
    this.disconnect()

    // don't specify subprotocol, our Qt Websocket server doesn't support that
    var protocol = 'ws://'
    if (location.protocol === 'https:') 
        protocol='wss://'

    this.webSocket = new WebSocket(protocol+server+":" + port);
    this.webSocket.binaryType = 'arraybuffer';
    this.webSocket.onopen = this.onopen.bind(this);
    this.webSocket.onclose = this.onclose.bind(this);
    this.webSocket.onmessage = this.onmessage.bind(this);
}

MessagingClient.prototype.disconnect = function() {
    if (this.webSocket != null) {
        this.webSocket.close()
        this.webSocket = null
    }
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
    if(typeof this.onclosed === "function")
    {
        this.onclosed();
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

MessagingClient.prototype.clearLogs = function () 
{
    sl = new ClearLogs();
    this.send(sl);
}
