/*
 *  The MsgTools core module for web apps.
 * This module exposes a number of connectivity and utility functions 
 * and classes available for writing web apps based on MsgTools.
 */

// TODO: Take this out of global space!!!
 var MessageDictionary = {}

 var msgtools = (function() {

    /*
     * Message registration and lookup
     */
    function registerMessage(msg) {

    }

    function lookupMessage(msgId) {

    }

    /**
     * MsgServer client class.  This class communicates over Websockets and is 
     * designed to run in a browser.  It provides basic connectivity events
     * mirroring the underlying Websocket and also encapsulates some core MsgTools
     * logic for identifying the client by name, and masking
     */
    class MessagingClient extends EventTarget {
        /**
         * Contruct a new MessagingClient
         * @param {string} name - the name of this messaging client.  Will be emitted on the Connect
         * message if Connect is defined and you request it.  If undefined we don't send a connect message.
         * @param {Window} hostWindow - the host window for the application (will be used to infer
         * if we should use a secure socket.  Overerides the secureSocket parameter.  If hostWindow
         * and has a ws and/or port query param, this class will use these values for the server and port
         * when connecting.
         */
        constructor(name='', hostWindow=null) {
            super()
            this.m_Name = name
            this.m_WebSocket = null
            this.m_HostWindow = hostWindow
        }

        /**
         * Connect to the target websocket server.  If a host window was provided in the constructor
         * then this method will apply a priority order for determining the server and port to use:
         * If the user passes a server and port that are not defaults, these will always be used first
         * If the user passes a default server or port, and a host window was provided then this class will
         * use the host window query params ws and port for the server and port respectively.
         *
         * @param {Map} - Map of options as follows
         * 'server' - IP or hostname of the target server. Default = 127.0.0.1
         * 'port' - port number of the target server.  Default = 5679
         * 'secureSocket' - Set to true if you want to use a secure socket.  If you want the client to 
         * automatcally select secure or insecure sockets based on the page souce then pass a host window
         * into the constructor and set secureSocket to false.  Default false.
         * 'subscriptionMask - uint32 mask for messages of interest - 0=don't care, 1=accept only.  
         * Default=0 (accept all)
         * 'subscriptionValue - uint32 value for a message of interest. Default = 0 (all messages).'
         */
        connect(options) {
            // Setup defaults...
            var server = '127.0.0.1'
            var port = 5679
            var secureSocket = false
            var subscriptionMask = 0
            var subscriptionValue = 0

            // Override defaults...
            if (options !== undefined && options !== null && options instanceof Map) {
                server = options.has('server') ? options.get('server') : server
                port = options.has('port') ? options.get('port') : port
                secureSocket = options.has('secureSocket') ? options.get('secureSocket') : secureSocket
                subscriptionMask = options.has('subscriptionMask') ? 
                    options.get('subscriptionMask') : subscriptionMask
                subscriptionValue = options.has('subscriptionValue') ? 
                    options.get('subscriptionValue') : subscriptionValue
            }

            // If we're already connected then disconnect the old socket and let it go...
            if ( this.m_WebSocket !== null ) {
                this.disconnect()
            }

            var protocol = 'ws://'
            if ((this.m_HostWindow != null && this.m_HostWindow.location.protocol === 'https:') || secureSocket) { 
                protocol='wss://'
            }

            // Apply server and port logic as outlined above
            if (this.m_HostWindow !== null) {
                var url = new URL(this.m_HostWindow.location)
                if (url.searchParams.has('ws') && server === '127.0.0.1') {
                    server = url.searchParams.get('ws')
                }
                if (url.searchParams.has('port') && port === 5679) {
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
                            if (typeof Connect == 'function') {
                                var cm = new Connect();
                                cm.SetNameString(''+this.m_Name);
                                this.sendMessage(cm);
                                sentConnected = true
                            }

                            // default values will make us receive all messages
                            if (typeof MaskedSubscription == 'function') {
                                var sm = new MaskedSubscription();
                                sm.SetMask(subscriptionMask)
                                sm.SetValue(subscriptionValue)
                                this.sendMessage(sm);
                                sentSubscription = true
                            }

                            // Request log status
                            if (typeof QueryLog == 'function') {
                                var ql = new QueryLog()
                                this.sendMessage(ql)
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
                                sentMask: sentSubscription
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
                        var id = hdr.GetMessageID()
                        var strId = String(id >>> 0)
                        if(strId in MessageDictionary)
                        {
                            var msgClass = MessageDictionary[strId]
                            msg = new msgClass(event.data)
                        }
                        else {
                            msg = new UnknownMsg(event.data)
                        }

                        // If this is a log status message then raise a special event for that
                        // Otherwise emit as a generic message
                        if (strId==LogStatus.prototype.MSG_ID) {
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
                                    message: msg
                                }
                            })

                            this.dispatchEvent(evt)

                            if(typeof this.onconnect === "function") {
                                this.onmessage(msg);
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
         * return true if the message was sent, otherwise false
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
                // 1000 is a normal/expected closure
                this.m_WebSocket.close(1000, 'disconnect() called')
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
         * Function callback called when  we've connected.  Simple Event with no detail.
         */
        // onconnected

        /**
         * Function callback called when a new Websocket message arrives.  Adhered to the same
         * contract as Websocket's onmessage (e.g. a MessageEvent is passed)
         */
        // onmessage

        /**
         * Function callback called when the underlying socket connection is disconnected.
         */
        // ondisconnected

        /**
         * Function callback called when there is an error - forwarded from the underlying Websocket
         * Also raised if the incoming message is not a known BMAP message
         */
        // onerror

        /**
         * Function callback called when we receive a log status message (will passs a LogStatus message)
         */
        // onlogstatus
    }

    // Module Exports...
    return {
        registerMessage : registerMessage,
        lookupMessage : lookupMessage,
        MessagingClient : MessagingClient
    }
})()