/*
 * The MsgTools core module for web apps.
 * This module exposes a number of connectivity and utility functions 
 * and classes available for writing web apps based on MsgTools.
 *
 * This module is Promises friendly where needed
 */

if (typeof msgtools !== "undefined") {
    console.log('msgtools already loaded')
} else {

 var msgtools = (function() {
    // Used to store a dictionary of all messages - key is the msg ID,
    // and the value is a reference to the message class itself
    var MessageDictionary = new Map();
    // same, but mapping from name to message class.
    var MessageNameDictionary = new Map();
    var MessageClassTree = Object.create(null);

    // Base messasge directory we load generated messages from
    // You must call load to initialize this method and load all
    // of our dependent messages.
    var msgDir = undefined
    var dependenciesLoaded = false
    var optionalMessages = new Set()

    /**
     * Set the base directory from which we should load messages. 
     *
     * This method not only initializes the base directory, but it also triggers loading
     * of module dependent messages (unless already loaded).  Of most import is the 
     * headers.NetworkHeader message which serves as a base header/template for ALL messages.
     *
     * @param {string} baseMsgDir - The base message directory for generated messages.
     * typically ending with obj/CodeGenerator/Javascript. Can be relative or absolute 
     * according to your app needs.
     *
     * @return A Promise that can be used to wait for, and confirm dependencies are loaded
     * If an error occurs the error response is an array of message urls that failed to load.
     */
    function load(baseMsgDir, msgs) {
        // First set the base directory
        if (baseMsgDir.length > 0 && baseMsgDir[baseMsgDir.length-1] != '/')
            baseMsgDir += '/'

        msgDir = baseMsgDir

        // If we were handed a single message then wrap it in an array
        // so we can symmetrically process one or multiple...
        if (msgs instanceof Array == false )
            msgs = [msgs]
        
        // All the messages this module depends on
        let dependencies = ['Network.Connect', 'Network.MaskedSubscription', 
            'Network.StartLog', 'Network.StopLog', 'Network.LogStatus', 'Network.QueryLog', 
            'Network.ClearLogs', 'Network.Note']

        // Create a set of optional messages
        optionalMessages = new Set(dependencies)

        // Network header is ALWAYS required, and should be the first because
        // other messages depend on it
        dependencies = ['headers.NetworkHeader'].concat(dependencies)
        dependencies = dependencies.concat(msgs);

        return new Promise((resolve, reject)=>{
            if (dependenciesLoaded == false)
                loadMessages(dependencies, msgDir)
                    .then(()=> {
                        dependenciesLoaded = true
                        resolve()
                    })
                    .catch(error=>{
                        dependenciesLoaded = false
                        reject(error)
                    })
            else
                resolve()
        })
    }

    /**
     * Pass in a list of messages relative to the baseMsgDir to load and register
     *
     * @param {string|Array} msgs - a list (or singular) message 'module' name.  These names should map to the 
     * directory structure of your message tree.  For example if we are loading headers/NetworkHeader.js
     * you would specify headers/NetworkHeader or headers.NetworkHeader as the message name.  This function
     * will take care of the base directory mapping, and make your message request a proper url for script loading.
     *
     * @return A Promise for async loading.  The error response will be an array of urls we couldn't load
     */
    function loadMessages(msgs) {
        return new Promise((resolve, reject)=> {

            var errors = new Array()
            var scriptsProcessed = 0

            msgs.forEach(function(msg, index, array) {
                // In case the user likes headers.NetworkHeader vs. header/NetworkHeader
                msgId = msg.replace(/\//g, '.')
                msg = msg.replace(/\./g, '/') 

                url = msgDir + msg + '.js'

                loadScript(url, msgId, (event)=>{
                    if (event.type == 'load')
                        scriptsProcessed++
                    else if (event.type == 'error' || event.type == 'abort') {
                        scriptsProcessed++

                        // If this isn't an optional message than tag it as an error
                        if (optionalMessages.has(event.srcElement.id) == false ) {
                            errors.push(event.srcElement.src)
                        }
                    }
                    // Done?
                    if (scriptsProcessed == msgs.length)
                        if (errors.length == 0)
                            resolve()
                        else
                            reject(errors)
                })
            })
        })
    }

    /*
     * Message registration.  This is called by each message as it loads.  Unless you're hand crafting your
     * own message outside the generator, you shouldn't need this...
     */
    function registerMessage(id, msgClass) {
        MessageDictionary.set(id, msgClass);
        var name = msgClass.prototype.MsgName();
        MessageNameDictionary.set(name, msgClass);
        
        var nested = MessageClassTree;
        var parts = name.split(".");
        for(var i=0; i<parts.length; i++) {
            part = parts[i];
            if(!(part in nested)) {
                if(i < parts.length-1) {
                    nested[part] = Object.create(null);
                } else {
                    nested[part] = msgClass;
                }
            }
            nested = nested[part];
        }
    }

    /**
     * Dynamic script loading - courtesy of Dhaval Shah
     * https://stackoverflow.com/questions/21294/dynamically-load-a-javascript-file
     * A few tweaks made to the callback events
     *
     * @param {string} the url to load
     *
     * @param {callback} a readystatechange/onload callback handler you can use to determine
     * when the script is done loading.
     */
    function loadScript(url, id, callback)
    {
        if ( document.getElementById(id) != null )
        {  
            // Don't bother creating a new script tag.
            // Just report it as ok.  If the caller didn't 
            // handle an error previously not our problem.
            callback(new Event('load'))
        }
        else
        {
           var head = document.getElementsByTagName('head')[0];
           var script = document.createElement('script');
           script.type = 'text/javascript';
           script.src = url;
           script.id = id;

           // then bind the event to the callback function 
           // there are several events for cross browser compatibility
           script.onload = callback;
           script.onerror = callback;
           script.onabort = callback;

           // fire the loading

          head.appendChild(script);
        }
    }
    
    class DelayedInit {
        static add(w) {
            if(DelayedInit.alreadyInitialized) {
                //console.log("    DelayedInit: added without delay");
                w.init();
            } else {
                //console.log("    DelayedInit.add() NOT adding to list");
                DelayedInit.widgets.push(w);
            }
        }
        static init() {
            while(DelayedInit.widgets.length > 0) {
                DelayedInit.widgets.pop().init();
            }
            DelayedInit.alreadyInitialized = true;
        }
    }
    //when running in a grafana panel, msgtools gets loaded once and this array is initialized to empty,
    //but widgets are put into it again and again when the Text panel HTML content is edited!
    //maybe this needs to be a hash table with a static key, so each thing is only put in once?
    //or maybe widgets need to remove themselves when they are destroyed?
    //how, though?  javascript has no concept of destructor!?!?!
    DelayedInit.widgets = [];
    DelayedInit.alreadyInitialized = false;
    class MessageDispatch {
        constructor() {
            // a lookup table of a list of listeners for each message ID
            this.m_listeners = {};
            // a cache of the last received message of each ID.
            // used to give new listeners the last received message
            // when they are created
            this.m_rxCache = {};
        }
        
        register(id, handler) {
            if(!(id in this.m_listeners)) {
                this.m_listeners[id] = [];
            }
            this.m_listeners[id].push(handler);
            if(id in this.m_rxCache) {
                handler(this.m_rxCache[id]);
            }
        }

        remove(id, handler) {
            let listeners = this.m_listeners[id];
            if (listeners !== undefined) {
                listeners.delete(handler);
            }
        }
        
        deliver(msg) {
            const id = msg.hdr.GetMessageID();
            let listeners = this.m_listeners[id];
            this.m_rxCache[id] = msg;
            if (listeners !== undefined) {
                for( let l of listeners ) {
                    l(msg);
                }
            }
        }
    }

    /**
     * Message client class.  This class communicates over Websockets and is 
     * designed to run in a browser.  It provides basic connectivity events
     * mirroring the underlying Websocket and also encapsulates some core MsgTools
     * logic for identifying the client by name, and masking
     */
    class MessageClient {
        /**
         * Contruct a new MessageClient
         *
         * @param {string} name - the name of this messaging client.  Will be emitted on the Connect
         * message if Connect is defined and you request it.  If undefined we don't send a connect message.
         *
         * @param {Window} hostWindow - the host window for the application (will be used to infer
         * if we should use a secure socket.  Overerides the secureSocket parameter.  If hostWindow
         * and has a ws and/or port query param, this class will use these values for the server and port
         * when connecting.
         */
        constructor(name='', hostWindow=null, subscriptionMask = 0, subscriptionValue = 0) {
            if (dependenciesLoaded==false)
                throw 'You must call load() before a MessageClient can be created.'

            // make a MessageClient easily globally accessible.
            msgtools.client = this;
            msgtools.DelayedInit.init();

            this.m_Name = name
            this.m_WebSocket = null
            this.m_HostWindow = hostWindow
            this.m_subscriptionMask = subscriptionMask;
            this.m_subscriptionValue = subscriptionValue;
        }

        /**
         * Connect to the target websocket server.  If a host window was provided in the constructor
         * then this method will apply a priority order for determining the server and port to use:
         * If the user passes a server and port that are not defaults, these will always be used first
         * If the user passes a default server or port, and a host window was provided then this class will
         * use the host window query params ws and port for the server and port respectively.
         *
         * @param {Map} - Map of options as follows:
         *  'server' - IP or hostname of the target server. Default = 127.0.0.1 - this will override window
         *  'port' - port number of the target server.  Default = 5679 - this will override window
         *  'secureSocket' - Set to true if you want to use a secure socket.  If you want the client to 
         *  automatically select secure or insecure sockets based on the page source then pass a host window
         *  into the constructor and set secureSocket to false.  Otherwise this option will always override 
         *  the window.  Default false.
         */
        connect(options) {
            // Setup defaults...
            var server = '127.0.0.1'
            var port = 5679
            var secureSocket = false
            var serverOption = false
            var portOption = false

            // Override defaults...
            if (options !== undefined && options !== null && options instanceof Map) {
                if (options.has('server')) {
                    if(options.get('server') != "") {
                        server = options.get('server')
                        serverOption = true
                    }
                }

                if (options.has('port')) {
                    port = options.get('port')
                    portOption = true
                } 

                secureSocket = options.has('secureSocket') ? options.get('secureSocket') : secureSocket
            }

            // If we're already connected then disconnect the old socket and let it go...
            if ( this.m_WebSocket !== null ) {
                this.disconnect()
            }

            var protocol = 'ws://'
            if ((this.m_HostWindow != null && this.m_HostWindow.location.protocol === 'https:') || secureSocket) { 
                protocol='wss://'
            }

            // Apply server and port logic as outlined above - note that if a server or port option
            // was specified that will override the query params here
            if (this.m_HostWindow !== null) {
                var url = new URL(this.m_HostWindow.location)
                if (serverOption == false && url.searchParams.has('ws') && server === '127.0.0.1') {
                    server = url.searchParams.get('ws')
                }
                if (portOption === false && url.searchParams.has('port') && port === 5679) {
                    port = url.searchParams.get('port')
                }
            }

            try {
                // Create a new Websocket for our comms...
                this.m_WebSocket = new WebSocket(protocol + server + ':' + port);
                this.m_WebSocket.binaryType = 'arraybuffer';

                this.m_WebSocket.onopen = this.on_ws_open.bind(this);
                this.m_WebSocket.onclose = this.on_ws_close.bind(this);
                this.m_WebSocket.onmessage = this.on_ws_message.bind(this);
                this.m_WebSocket.onerror = this.on_ws_error.bind(this);
            }
            catch (e) {
                if ( this.m_WebSocket !== null) {
                    this.m.WebSocket.close()
                }

                this.m_WebSocket = null

                throw e
            }
        }
                
        // Open event indicating the WS is open
        on_ws_open(event) {
            try {
                if (typeof Connect == 'function') {
                    var cm = new Connect();
                    cm.SetNameString(''+this.m_Name);
                    this.sendMessage(cm);
                }

                if (typeof MaskedSubscription == 'function') {
                    var sm = new MaskedSubscription();
                    sm.SetMask(this.m_subscriptionMask)
                    sm.SetValue(this.m_subscriptionValue)
                    this.sendMessage(sm);
                }
            }
            catch(e) {
                // Just move on...
            }

            if(typeof this.onconnected === "function") {
                this.onconnected();
            }
        }

        on_ws_message(event) {
            var msg = null;
            var hdr = new NetworkHeader(event.data);
            var id = hdr.GetMessageID();
            if(MessageDictionary.has(id))
            {
                var msgClass = MessageDictionary.get(id);
                msg = new msgClass(event.data);
            }
            else {
                msg = new UnknownMsg(event.data);
            }

            // do message delivery based on message ID
            MessageClient.dispatch.deliver(msg)
                
            if(typeof this.onmessage === "function") {
                this.onmessage(msg);
            }
        }

        on_ws_close(event) {
            if(typeof this.ondisconnected === "function") {
                this.ondisconnected();
            }       

            // cleanup the WebSocket
            this.m_WebSocket = null
        }

        on_ws_error(event) {
            if(typeof this.onerror === "function") {
                this.onerror(event);
            }            
        }
    
        /**
         * Send a message on the underlying Websocket.
         *
         * @param {object} msg - We expect a MsgTools compatible message.  Meaning 
         * the message has a NetworkHeader and a m_data_buffer payload.
         *
         * @return true if the message was sent, otherwise false
         */
        sendMessage(msg) {
            var retVal = false
            if (this.isConnected) {
                try {
                    var buf = msg.m_data.buffer;
                    var lenFromHdr = msg.hdr.MSG_SIZE + msg.hdr.GetDataLength();
                    if(lenFromHdr < msg.m_data.buffer.byteLength) {
                        buf = msg.m_data.buffer.slice(0,lenFromHdr);
                    }
                    this.m_WebSocket.send(buf);                    
                    retVal = true
                }
                catch(e) {
                }
            }

            return retVal
        }

        /**
        * If we're connected then disconnect
        */
        disconnect() {
            if (this.m_WebSocket !== null) {
                try {
                    // 1000 is a normal/expected closure
                    this.m_WebSocket.close(1000, 'disconnect() called')
                }
                finally {
                }
            }        
        }

        /**
         * If we're connected return true, else return false
         */
        get isConnected() { 
            if (this.m_WebSocket !== null) {
                return this.m_WebSocket.readyState === 1 // 1 = OPEN aka connected and ready to communiate
            }

            return false
        }

        /**
         * undefined if we aren't connected, else the readyState value of the
         * underlying Websocket - See the WebSocket specification for details.
         */
        get readyState() {
            if (this.m_WebSocket !== null) {
                return m_WebSocket.readyState;
            }

            return -1;
        }

        // Virtual functions that subclasses can implement:
        // onconnected
        // onmessage
        // ondisconnected
        // onerror
    }
    MessageClient.dispatch = new MessageDispatch();

    /**
     * If we have no idea what a message is (because it's definition wasn't loaded) then return an UnknownMsg
     * in the onmessage event callback.  This allows reflection to inspect a "unknown" message
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

    /**
     * Convert the given msg to JSON
     *
     * @param {object} obj - Assumed to be a message with a network header.  Convert it to 
     * a JSON string suitable for printing etc...
     * 
     * @return JSON string of the given message
     */
    function toJSON(obj) {
        // console.log("JSON for " + obj.MSG_NAME + ", ID=",+obj.MSG_ID+", "+obj.MSG_SIZE+" bytes")
        var jsonStr = '{"'+obj.MsgName()+'": ';
        jsonStr += JSON.stringify(obj.toObject());
        jsonStr += '}'
        return jsonStr;
    }

    /**
     * Retrieve the websocket server params from the given window
     * 
     * @param {Window} hostWindow - the host window from which to rerieve query params
     * we're looking specifically for ws and port as our server and port params respectively.
     *
     * @return object with websocketServer and websocketPort set to our defaults (127.0.0.1 and 5679)
     * or whatever we handed in on the query params
     */
    function getWebsocketURLParams(hostWindow) {
        var url = new URL(hostWindow.location)
        var ws = "127.0.0.1"
        var port = 5679
        if (url.searchParams.has('ws'))
            ws = url.searchParams.get('ws')
        if (url.searchParams.has('port'))
            port = url.searchParams.get('port')

        return {websocketServer: ws, websocketPort:port}    
    }
    
    function findFieldInfo(msgClass, fieldName) {
        for(var i=0; i<msgClass.prototype.fields.length; i++) {
            var fieldInfo = msgClass.prototype.fields[i];
            if(fieldInfo.name == fieldName) {
                return fieldInfo;
            }
        }
        return null;
    }
    
    function findMessageByName(msgname) {
        return MessageNameDictionary.get(msgname);
    }

    // Module Exports...
    return {
        load : load,
        registerMessage : registerMessage,
        findMessageByName : findMessageByName,
        findFieldInfo : findFieldInfo,
        MessageClient : MessageClient,
        DelayedInit : DelayedInit,
        UnknownMsg : UnknownMsg,
        toJSON : toJSON,
        getWebsocketURLParams : getWebsocketURLParams,
        messageNameDictionary : MessageNameDictionary,
        msgs  : MessageClassTree
    }
})()

window.msgtools = msgtools;
}
