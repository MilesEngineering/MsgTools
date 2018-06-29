/*
 * The MsgTools core module for web apps.
 * This module exposes a number of connectivity and utility functions 
 * and classes available for writing web apps based on MsgTools.
 *
 * This module is Promises frienndly where needed
 */


 var msgtools = (function() {
    // Used to store a dictionary of all messages - key is the msg ID,
    // and the value is a reference to the message class itself
    var MessageDictionary = new Map()

    // Base messasge directory we load generated messages from
    // You must call setMsgDirectory to initialize this method and load all
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
    function setMsgDirectory(baseMsgDir) {
        // First set the base directory
        if (baseMsgDir.length > 0 && baseMsgDir[baseMsgDir.length-1] != '/')
            baseMsgDir += '/'

        msgDir = baseMsgDir

        // All the messages this module depends on
        let dependencies = ['Network.Connect', 'Network.MaskedSubscription', 
            'Network.StartLog', 'Network.StopLog', 'Network.LogStatus', 'Network.QueryLog', 
            'Network.ClearLogs', 'Network.Note']

        // Create a set of optional messages
        optionalMessages = new Set(dependencies)

        // Network header is ALWAYS required, and should be the first because
        // other messages depend on it
        dependencies = ['headers.NetworkHeader'].concat(dependencies)

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
     * @param {string} baseMsgDir - override our module base directory to load one or more messages from
     * the indicated base instead.
     *
     * @return A Promise for async loading.  The error response will be an array of urls we couldn't load
     */
    function loadMessages(msgs, baseMsgDir=undefined) {
        return new Promise((resolve, reject)=> {

            // If we were handed a single message then wrap it in an array
            // so we can symmetrically process one or multiple...
            if (msgs instanceof Array == false )
                msgs = [msgs]

            var baseDir = baseMsgDir === undefined ? msgDir : baseMsgDir
            if (baseDir.length > 0 && baseDir[baseDir.length-1] != '/')
                baseDir += '/'

            var errors = new Array()
            var scriptsProcessed = 0

            msgs.forEach(function(msg, index, array) {
                // In case the user likes headers.NetworkHeader vs. header/NetworkHeader
                msgId = msg.replace(/\//g, '.')
                msg = msg.replace(/\./g, '/') 

                url = baseDir + msg + '.js'

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
    function registerMessage(id, msg) {
        MessageDictionary.set(id, msg)
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

    /**
     * MsgServer client class.  This class communicates over Websockets and is 
     * designed to run in a browser.  It provides basic connectivity events
     * mirroring the underlying Websocket and also encapsulates some core MsgTools
     * logic for identifying the client by name, and masking
     */
    class MessagingClient {
        /**
         * Contruct a new MessagingClient
         *
         * @param {string} name - the name of this messaging client.  Will be emitted on the Connect
         * message if Connect is defined and you request it.  If undefined we don't send a connect message.
         *
         * @param {Window} hostWindow - the host window for the application (will be used to infer
         * if we should use a secure socket.  Overerides the secureSocket parameter.  If hostWindow
         * and has a ws and/or port query param, this class will use these values for the server and port
         * when connecting.
         */
        constructor(name='', hostWindow=null) {

            // Because Safari doesn't support EventTarget as an actual constructable class, and Chrome
            // appears to spuriously send events to disconnected DOM elements that result in 
            // unexpected messages to client we'll need to implement our own EventTarget API.
            this.m_Listeners = {}
            this.m_Listeners.message = new Set()
            this.m_Listeners.connected = new Set()
            this.m_Listeners.disconnected = new Set()
            this.m_Listeners.error = new Set()
            this.m_Listeners.logstatus = new Set()

            if (dependenciesLoaded==false)
                throw 'You must call setMsgDirectory() before a MessageClient can be created.'

            this.m_Name = name
            this.m_WebSocket = null
            this.m_HostWindow = hostWindow
        }

        //
        // Emulate Event Target
        //

        /**
         * Add an event listener.  
         * @param {string} - The type of message this listener is interested in.  Valid values are
         * message, connected, disconnected, error, logstatus.
         * @param {EventListener} - The event listener to register
         */
        addEventListener(type, listener) {
            var listeners = this.m_Listeners[type]
            if (listeners !== undefined) {
                listeners.add(listener)
            }
        }

        /**
         * Removes the indicated listener from the indicated messsge type
         * @param {string} type - See add listener for the list of valid types
         * @param {EventListener} - The event listener to remove
         */
        removeEventListener(type, listener) {
            var listeners = this.m_Listeners[type]
            if (listeners !== undefined) {
                listeners.delete(listener)
            }
        }
        
        /**
         * Send the indicated event to all registered listeners
         */
        dispatchEvent(event) {
            var listeners = this.m_Listeners[event.type]
            if (listeners !== undefined) {
                for( let l of listeners ) {
                    try {
                        if ( typeof(l) == 'function') 
                            l(event)
                        else if (l.handleEvent !== undefined)
                            l.handleEvent(event)
                    }
                    catch(e) {
                        // Nothing - carry on
                    }
                }
            }
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
         *  'subscriptionMask - uint32 mask for messages of interest - 0=don't care, 1=accept only.  
         *  Default=0 (accept all)
         *  'subscriptionValue - uint32 value for a message of interest. Default = 0 (all messages).'
         *  'suppressConnect' - true if you don't want to send a Connect message on connection. Default=false.
         *  'suppressMaskedSubscription' - true if you don't want to send a MaskedSubscription message on connection.
         *   Default=false.
         *  'suppressQueryLog' - true if you don't want to send a QueryLog message on connection.
         */
        connect(options) {
            // Setup defaults...
            var server = '127.0.0.1'
            var port = 5679
            var secureSocket = false
            var subscriptionMask = 0
            var subscriptionValue = 0
            var suppressConnect = false
            var suppressMaskedSubscription = false
            var suppressQueryLog = false
            var serverOption = false
            var portOption = false

            // Override defaults...
            if (options !== undefined && options !== null && options instanceof Map) {
                if (options.has('server')) {
                    server = options.get('server')
                    serverOption = true
                }

                if (options.has('port')) {
                    port = options.get('port')
                    portOption = true
                } 

                secureSocket = options.has('secureSocket') ? options.get('secureSocket') : secureSocket
                subscriptionMask = options.has('subscriptionMask') ? 
                    options.get('subscriptionMask') : subscriptionMask
                subscriptionValue = options.has('subscriptionValue') ? 
                    options.get('subscriptionValue') : subscriptionValue
                suppressConnect = options.has('suppressConnect') ?
                    options.get('suppressConnect') : suppressConnect
                suppressMaskedSubscription = options.has('suppressMaskedSubscription') ?
                    options.get('suppressMaskedSubscription') : suppressMaskedSubscription
                suppressQueryLog = options.has('suppressQueryLog') ?
                    options.get('suppressQueryLog') : suppressQueryLog
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
              
                var eventListener = (event)=>{

                    // Open event indicating the WS is open
                    if (event.type === 'open') {
                        var sentConnected = false
                        var sentSubscription = false
                        try {
                            if (suppressConnect == false && typeof Connect == 'function') {
                                var cm = new Connect();
                                cm.SetNameString(''+this.m_Name);
                                this.sendMessage(cm);
                                sentConnected = true
                            }

                            // default values will make us receive all messages
                            if (suppressMaskedSubscription == false && typeof MaskedSubscription == 'function') {
                                var sm = new MaskedSubscription();
                                sm.SetMask(subscriptionMask)
                                sm.SetValue(subscriptionValue)
                                this.sendMessage(sm);
                                sentSubscription = true
                            }

                            // Request log status
                            var sentQueryLog = false
                            if (suppressQueryLog == false && typeof QueryLog == 'function') {
                                var ql = new QueryLog()
                                this.sendMessage(ql)
                                sentQueryLog = true
                            }
                        }
                        catch(e) {
                            // Just move on...
                        }

                        // Dispatch an onconnected event with some hopefully 
                        // useful info...
                        var connectedEvent = new CustomEvent('connected', {
                            detail: {
                                connectionUrl: this.m_WebSocket.url,
                                sentConnected: sentConnected,
                                sentSubscription: sentSubscription,
                                sentLogQuery: sentQueryLog
                            }
                        })

                        this.dispatchEvent(connectedEvent)

                        if(typeof this.onconnected === "function") {
                            this.onconnected(connectedEvent);
                        }
                    }

                    else if (event.type==='message') {
                        // TODO: At some point try to interpret log status
                        // or other specific messages and raise a specific event for that
                        var msg = null
                        var hdr = new NetworkHeader(event.data)
                        var id = hdr.GetMessageID() >>> 0;
                        if(MessageDictionary.has(id))
                        {
                            var msgClass = MessageDictionary.get(id)
                            msg = new msgClass(event.data)
                        }
                        else {
                            msg = new UnknownMsg(event.data)
                        }

                        // If this is a log status message then raise a special event for that
                        // Otherwise emit as a generic message
                        if (id==LogStatus.prototype.MSG_ID) {
                            var evt = new CustomEvent( 'logstatus',
                                { detail: {
                                    logIsOpen: msg.GetLogOpen(),
                                    logType: msg.GetLogFileType(),
                                    logFilename: msg.GetLogFileNameString()
                                }
                            })

                            this.dispatchEvent(evt)

                            if (typeof this.onlogstatus=='function') {
                                this.onlogstatus(evt)
                            }
                        }
                        else {
                            var evt = new CustomEvent('message', 
                                {detail: {
                                    message: msg,
                                    data: event.data
                                }
                            })

                            this.dispatchEvent(evt)

                            if(typeof this.onconnect === "function") {
                                this.onmessage(evt);
                            }
                        }
                    }

                    else if (event.type==='close') {
                        var disconnectedEvent = new CustomEvent( 'disconnected', {
                            detail: {
                                code: event.code,
                                reason: event.reason,
                                wasClean: event.wasClean
                            }
                        })

                        this.dispatchEvent(disconnectedEvent)

                        if(typeof this.ondisconnected === "function") {
                            this.ondisconnected(disconnectedEvent);
                        }       

                        // Stop receiving events and cleanup the WebSocket
                        this.m_WebSocket.removeEventListener('open', eventListener)
                        this.m_WebSocket.removeEventListener('message', eventListener)
                        this.m_WebSocket.removeEventListener('close', eventListener)
                        this.m_WebSocket.removeEventListener('error', eventListener)
                        this.m_WebSocket = null
                    }

                    else if (event.type==='error') {
                        if(typeof this.onerror === "function") {
                            this.onerror(event);
                        }            
                    }
                }

                // Sign up for WS events...
                this.m_WebSocket.addEventListener('open', eventListener)
                this.m_WebSocket.addEventListener('message', eventListener)
                this.m_WebSocket.addEventListener('close', eventListener)
                this.m_WebSocket.addEventListener('error', eventListener)
            }
            catch (e) {
                if ( this.m_WebSocket !== null) {
                    this.m.WebSocket.close()
                    this.m_WebSocket.removeEventListener('open', eventListener)
                    this.m_WebSocket.removeEventListener('message', eventListener)
                    this.m_WebSocket.removeEventListener('close', eventListener)
                    this.m_WebSocket.removeEventListener('error', eventListener)
                }

                this.m_WebSocket = null

                throw e
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
                    this.m_WebSocket.removeEventListener('open', eventListener)
                    this.m_WebSocket.removeEventListener('message', eventListener)
                    this.m_WebSocket.removeEventListener('close', eventListener)
                    this.m_WebSocket.removeEventListener('error', eventListener)
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
                return m_WebSocket.readyState
            }

            return -1
        }

        //===== Server logging interface
        startLogging() {
            if (this.m_WebSocket !== null && typeof StartLog == 'function') {
                var sl = new StartLog();
                sl.SetLogFileType("Binary")
                this.sendMessage(sl)
            }
        }

        stopLogging() {
            if (this.m_WebSocket !== null && typeof StopLog == 'function') {
                var sl = new StopLog()
                this.sendMessage(sl)
            }
        }

        clearLogs() {
            if (this.m_WebSocket !== null && typeof ClearLogs == 'function') {
                var sl = new ClearLogs()
                this.sendMessage(sl)
            }
        }

        logNote(message) {
            if (this.m_WebSocket !== null && typeof Note == 'function') {
                var sl = new Note()
                sl.SetTextString(message)
                this.sendMessage(sl)
            }
        }

        //===== EVENTS 
        // These are all function pointers to your preferred callback.
        //All of these events are also dispatched as part of this class as a 
        //EventTarget - you may use addEventListener to register multiple handlers 
        //if needed

        /**
         * Function callback called when  we've connected.  Emits a CustomEvent that
         * inlcudes the WS url, and booleans indicated if a Connect and Subscription
         * and LoqQuery messages were sent.
         */
        // onconnected

        /**
         * Function callback called when a new Websocket message arrives.  Emits a CustomEvent
         * with the parsed message (and raw data) as part of the detail.
         */
        // onmessage

        /**
         * Function callback called when the underlying socket connection is disconnected.
         * Emits a CustomEvent with details about why the connection was closed.
         */
        // ondisconnected

        /**
         * Function callback called when there is an error - forwarded from the underlying Websocket
         */
        // onerror

        /**
         * Function callback called when we receive a log status message (will passs a LogStatus message)
         */
        // onlogstatus
    }

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
     * Convert the array buffer to a hex string
     *
     * @param {ArrayBuffer} buffer - the buffer to convert to a string
     *
     * @return hex string representation of the given buffer
     */
    function buf2hex(buffer) { // buffer is an ArrayBuffer
      return Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
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

    // Make a pretty log output.  This is also an example of how to iterate over 
    // the fields of a message, getting metadata about each field (and bitfield), 
    // and getting the value of the field using the get function called with 
    // bracket notation obj[fnName](), instead of obj.fn()
    function prettyPrint(obj) {
        var ret = "Reflection information obtained by iterating over list of fields\n";
        var proto = Object.getPrototypeOf(obj);
        for(var i=0; i<proto.fields.length; i++)
        {
            var field = proto.fields[i];
            var numBitfields = field.bitfieldInfo.length;
            if(numBitfields == 0)
            {
                ret += "name: " + field.name;
                if(field.count != 1)
                    ret += "[" + field.count + "]";
                ret +=", type="+field.type+ ", value="+obj[field.get]()+", " + "desc=" + field.description + ", range=("+field.minVal + ","+field.maxVal+")"+ "\n";
            }
            else
            {
                for(var j=0; j<field.bitfieldInfo.length; j++)
                {
                    bitfield = field.bitfieldInfo[j];
                    ret += "name: " + field.name+"."+bitfield.name;
                    ret += ", type="+bitfield.type+", value="+obj[bitfield.get]()+", " + "desc=" + bitfield.description + ", range=("+bitfield.minVal + ","+bitfield.maxVal+")"+ "\n";
                }
            }
        }
        return ret;
    }

    // Module Exports...
    return {
        setMsgDirectory : setMsgDirectory,
        loadMessages : loadMessages,
        registerMessage : registerMessage,
        MessagingClient : MessagingClient,
        UnknownMsg : UnknownMsg,
        toJSON : toJSON,
        buf2hex : buf2hex,
        getWebsocketURLParams : getWebsocketURLParams,
        prettyPrint : prettyPrint
    }
})()