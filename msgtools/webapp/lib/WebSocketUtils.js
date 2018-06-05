'use strict';
//To-Do remove WebSocketUtils from global namespace 
//`connect-name` acts as a unique id to access MsgSocket 
//Pre-Requisites check of msgtools
//
var WebSocketUtils = {};

(function() {

    customElements.define('msgsocket-connector', class extends HTMLElement {
        static get observedAttributes() { return ['msg-client']; }
        constructor() {
            super();

            this.shadow = this.attachShadow({
                mode: 'open'
            });
            var style = document.createElement('style');
            style.innerHTML = `
            :host{
                all: initial;
                display: block;
                contain: content;
                text-align: center;
                background: linear-gradient(to left, var(--bg-color, white), transparent);                
            }
            input[type="button"]{

                cursor: pointer;
                background: var(--btn-bg-color, white);
                color: var(--btn-color, black);
                border-color: var(--btn-border-color, grey);
                border: var(--btn-border, .5px solid grey);
                border-radius: var(--btn-border-radius, 6px);
                box-shadow: var(--btn-box-shadow, 0 ,0 0px rgba(255, 255, 255, 1));
                margin-left: var(--btn-margin-left, 10px);
                margin-top: var(--btn-margin-top, 5px);
                margin-bottom: var(--btn-margin-bottom, 5px);
                margin-right: var(--btn-margin-right, 0px);
                width: var(--btn-width, auto);
                height: var(--btn-height, auto);     
                font-family: var(--btn-font-family, "Helvetica Neue", Helvetica, Arial, sans-serif);
                font-size: var(--btn-font-size, small);
                font-color: var(--btn-font-color, grey);
          

            }
            input[type="text"]{

                background: var(--txt-bg-color, white);
                color: var(--txt-color, black);
                border-color: var(--txt-border-color, grey);
                border: var(--txt-border, .5px solid grey);
                border-radius: var(--txt-border-radius, 2px);
                box-shadow: var(--txt-box-shadow, 0 ,0 0px none);
                margin-left: var(--txt-margin-left, 10px);
                margin-top: var(--txt-margin-top, 5px);
                margin-bottom: var(--txt-margin-bottom, 5px);
                margin-right: var(--txt-margin-right, 0px);
                width: var(--txt-width, auto);
                height: var(--txt-height, auto);
                font-family: var(--txt-font-family, "Helvetica Neue", Helvetica, Arial, sans-serif);
                font-size: var(--txt-font-size, small);

            }
            span{

                background: var(--span-bg-color, null);
                color: var(--span-color, black);
                border-color: var(--span-border-color, null);
                border: var(--span-border, null);
                border-radius: var(--span-border-radius, null);
                box-shadow: var(--span-box-shadow, 0 ,0 0px null);
                margin-left: var(--span-margin-left, 5px);
                margin-top: var(--span-margin-top, 5px);
                margin-bottom: var(--span-margin-bottom, 5px);
                margin-right: var(--span-margin-right, 0px);
                width: var(--span-width, auto);
                height: var(--span-height, auto);
                font-family: var(--span-font-family, "Helvetica Neue", Helvetica, Arial, sans-serif);
                font-size: var(--span-font-size, small);

            }
            `;
            this.shadow.appendChild(style);

        }

        connectedCallback() {

            var webSocketConnection = this;
            if (this.hasAttribute('hidden')) {
                this.style.display = "none"

            }

            this.ws = document.createElement('input');
            this.ws.setAttribute('id', 'ws');
            this.ws.setAttribute('type', 'text');
            this.ws.setAttribute('placeholder', 'Address');
            this.ws.setAttribute('onfocus', '');

            //Address By User - default '127.0.0.1'            
            var params = msgtools.getWebsocketURLParams(window) //msgtools.js 
            if (params.websocketServer === null || params.websocketServer === '') {
                var address = this.getAttribute('socket-address');
                if (address !== '' && address !== null) {
                    this.ws.setAttribute('value', address);
                } else {
                    this.ws.setAttribute('value', '127.0.0.1');
                }
            } else {
                this.ws.setAttribute('value', params.websocketServer);
            }
            this.shadow.appendChild(this.ws);

            //Port By User - default '5679'
            this.port = document.createElement('input');
            this.port.setAttribute('id', 'port');
            this.port.setAttribute('type', 'text');
            this.port.setAttribute('placeholder', 'Port');
            this.port.setAttribute('onfocus', '');
            this.port.setAttribute('size', "5");


            if (params.websocketPort === null || params.websocketPort === '') {
                var port = this.getAttribute('socket-port');
                if (port !== '' && port !== null) {
                    this.port.setAttribute('value', port);
                } else {
                    this.port.setAttribute('value', '5679');
                }
            } else {
                this.port.setAttribute('value', params.websocketPort);
            }
            this.shadow.appendChild(this.port);

            //Name By User - default 'NoName'
            this.display_name = document.createElement('span');
            var name = this.getAttribute('connect-name');
            if (name !== '' && name !== null) {
                this.name = name;
            } else {
                this.name = 'NoName'; // Better throw error !!!
            }
            name = this.name;
            this.display_name.innerHTML = name;
            this.shadow.insertBefore(this.display_name, this.ws);

            //Used for exposing each instance of msgSocket externally 
            WebSocketUtils[name] = {}

            this.connect_ele = document.createElement('input');
            this.connect_ele.setAttribute('id', 'connect');
            this.connect_ele.setAttribute('value', 'Connect');
            this.connect_ele.setAttribute('type', 'button');
            this.connect_ele.addEventListener('click', function() {

                var ws_value = webSocketConnection.ws.value;
                var port_value = webSocketConnection.port.value;

                if (ws_value !== '' && port_value !== '') {

                    var url = webSocketConnection.setURLParams();
                    if (window.history.state === null || window.history.state.path !== url.toString()) {
                        // Save state so you can bookmark etc
                        window.history.pushState({}, '', url.toString())
                        // Check msgSocket for this instance name already present ??
                        if (webSocketConnection.client === null || webSocketConnection.client === undefined) {
                            throw 'No Client Accquired'
                        } else {
                            // Open a new connection - the socket will take care of closing
                            // an one if present
                            if (webSocketConnection.connect_ele.getAttribute('value').toLowerCase().startsWith('connect')) {
                                console.log('Connecting %s:%s', ws_value, port_value)
                                webSocketConnection.webSocketStatus("Connecting", 'gold');
                                var options = new Map();
                                options.set('address', ws_value);
                                options.set('port', port_value);
                                webSocketConnection.client.connect();
                                if (webSocketConnection.hasAttribute('onclick-start'))
                                    eval(webSocketConnection.getAttribute('onclick-start'));

                            } else {
                                console.log('DisConnecting %s:%s', ws_value, port_value)
                                webSocketConnection.webSocketStatus("Disconnecting", 'gold');
                                webSocketConnection.client.disconnect();
                                if (webSocketConnection.hasAttribute('onclick-stop'))
                                    eval(webSocketConnection.getAttribute('onclick-stop'));
                            }
                        }
                    }

                } else {
                    webSocketConnection.webSocketStatus("Empty address or port", 'red', false);
                }
            }, false);
            this.shadow.appendChild(this.connect_ele);
            this.status = document.createElement('span');
            this.status.setAttribute('id', 'status');
            this.shadow.appendChild(this.status);

        }

        setURLParams() {
            var ws_value = this.ws.value;
            var port_value = this.port.value;
            var url = new URL(window.location)
            var urlParams = url.searchParams
            urlParams.set('ws', ws_value)
            urlParams.set('port', port_value)
            return url;
        }


        setupClient(client) {
            var webSocketConnection = this;

            console.log('[setupClient] Acquire msgClient from global ', WebSocketUtils[this.name].msgClient);
            client = WebSocketUtils[this.name].msgClient; //To-Do access the object instead of global 
            this.webSocketStatus("Connecting", 'gold');

            client.addEventListener('connected', function(response) {
                webSocketConnection.webSocketStatus("Connected", 'green');
                console.log('[WebSocketUtils] onconnect', response);
                webSocketConnection.connect_ele.setAttribute('value', 'Disconnect');

            }, false);
            client.addEventListener('open', function() {
                webSocketConnection.webSocketStatus("Open", 'blue');
                console.log('[WebSocketUtils] Open');

            }, false);

            client.addEventListener('disconnected', function() {
                webSocketConnection.webSocketStatus("Disconnected", 'red');
                console.log('[WebSocketUtils] Disconnected');
                webSocketConnection.connect_ele.setAttribute('value', 'Connect');

            }, false);

            client.addEventListener('close', function() {
                webSocketConnection.webSocketStatus("Closed", 'orange');
                console.log('[WebSocketUtils] Closed');

            }, false);

            client.addEventListener('error', function() {
                webSocketConnection.webSocketStatus("Error on", 'red');
                console.log('[WebSocketUtils] Error on');

            }, false);

            var options = new Map();
            options.set('server', this.ws.value)
            options.set('port', this.port.value)

            client.connect(options);

            return client;
        }

        webSocketStatus(status, color, display = true) {
            var socketStatus = this.status;
            if (socketStatus !== undefined && socketStatus !== null) {
                socketStatus.style.color = color;
                if (display) {
                    socketStatus.textContent = status + " ... " + this.ws.value + ":" + this.port.value;
                } else {
                    socketStatus.textContent = status;
                }

            }
        }

        disconnectedCallback() {
            //
        }

        attributeChangedCallback(name, oldValue, newValue) {

            switch (name) {
                case 'msg-client':
                    this.client = this.setupClient(newValue);
                    break;
                default:
                    console.log('Not implemented changed for', name);
                    throw 'Not implemented changed for' + name
            }


        }


    });



    customElements.define('msgsocket-logging', class extends HTMLElement {
        static get observedAttributes() { return ['msg-client']; }
        constructor() {
            super();
            this.shadow = this.attachShadow({
                mode: 'open'
            });
            var style = document.createElement('style');
            style.innerHTML = `
            :host{
                all: initial;
                display: block;
                contain: content;
                text-align: center;
                background: linear-gradient(to left, var(--bg-color, white), transparent);                
            }
            input[type="button"]{

                cursor: pointer;
                background: var(--btn-bg-color, white);
                color: var(--btn-color, black);
                border-color: var(--btn-border-color, grey);
                border: var(--btn-border, .5px solid grey);
                border-radius: var(--btn-border-radius, 6px);
                box-shadow: var(--btn-box-shadow, 0 ,0 0px rgba(255, 255, 255, 1));
                margin-left: var(--btn-margin-left, 10px);
                margin-top: var(--btn-margin-top, 5px);
                margin-bottom: var(--btn-margin-bottom, 5px);
                margin-right: var(--btn-margin-right, 0px);
                width: var(--btn-width, auto);
                height: var(--btn-height, auto);     
                font-family: var(--btn-font-family, "Helvetica Neue", Helvetica, Arial, sans-serif);
                font-size: var(--btn-font-size, small);
                font-color: var(--btn-font-color, grey);

            }
            input[type="text"]{

                background: var(--txt-bg-color, white);
                color: var(--txt-color, black);
                border-color: var(--txt-border-color, grey);
                border: var(--txt-border, .5px solid grey);
                border-radius: var(--txt-border-radius, 2px);
                box-shadow: var(--txt-box-shadow, 0 ,0 0px none);
                margin-left: var(--txt-margin-left, 10px);
                margin-top: var(--txt-margin-top, 5px);
                margin-bottom: var(--txt-margin-bottom, 5px);
                margin-right: var(--txt-margin-right, 0px);
                width: var(--txt-width, auto);
                height: var(--txt-height, auto);
                font-family: var(--txt-font-family, "Helvetica Neue", Helvetica, Arial, sans-serif);
                font-size: var(--txt-font-size, small);

            }
            `;
            this.shadow.appendChild(style);

        }

        connectedCallback() {

            var event_id = 1;
            //Name of Messaging Client 
            var name = this.getAttribute('connect-name');
            if (name !== '' && name !== null) {
                this.name = name;
            } else {
                throw 'Error :Usage <msgsocket-logging connect-name="testApp" > </msgsocket-logging>';
            }
            name = this.name;
            var webSocketLog = this;

            if (this.hasAttribute('hidden')) {
                this.style.display = "none"

            }

            this.actionLog = document.createElement('input');
            this.actionLog.setAttribute('id', 'logAction');
            this.actionLog.setAttribute('value', 'Start Logging');
            this.actionLog.setAttribute('type', 'button');
            this.actionLog.addEventListener('click', function(element) {
                if (webSocketLog.enableLogging) {
                    if (webSocketLog.actionLog.getAttribute('value').toLowerCase().startsWith("start")) {
                        // start logging
                        webSocketLog.client.startLogging();
                        if (webSocketLog.hasAttribute('onclick-start'))
                            eval(webSocketLog.getAttribute('onclick-start'));
                        console.log('[WebSocketUtils] start');
                    } else {
                        // stop logging
                        webSocketLog.client.stopLogging();
                        console.log('[WebSocketUtils] stop');
                        if (webSocketLog.hasAttribute('onclick-stop'))
                            eval(webSocketLog.getAttribute('onclick-stop'));
                    }
                }
            }, false);
            this.shadow.appendChild(this.actionLog);

            this.clearLog = document.createElement('input');
            this.clearLog.setAttribute('id', 'clearLog');
            this.clearLog.setAttribute('value', 'Clear Logs');
            this.clearLog.setAttribute('type', 'button');


            this.clearLog.addEventListener('click', function() {
                if (webSocketLog.enableLogging) {
                    if (confirm("This will delete all logs on the server app.  Are you sure?"))
                        webSocketLog.client.clearLogs();
                    //check if any function provided
                    if (webSocketLog.hasAttribute('onclick-clear'))
                        eval(webSocketLog.getAttribute('onclick-clear'));
                }
            }, false);
            this.shadow.appendChild(this.clearLog);

            this.comment = document.createElement('input');
            this.comment.setAttribute('id', 'logText');
            this.comment.setAttribute('placeholder', 'Enter Comment');
            this.comment.setAttribute('type', 'text');
            this.shadow.appendChild(this.comment);

            this.noteLog = document.createElement('input');
            this.noteLog.setAttribute('id', 'logNote');
            this.noteLog.setAttribute('value', 'Log Note');
            this.noteLog.setAttribute('type', 'button');
            this.noteLog.addEventListener('click', function(element) {
                if (webSocketLog.enableLogging) {
                    var txt = webSocketLog.comment.getAttribute('value');
                    if (txt) {
                        txt = "event" + event_id + ":" + txt;
                    } else {
                        txt = "event" + event_id;
                    }
                    event_id += 1;
                    console.log('[WebSocketUtils] LogNote', txt);
                    webSocketLog.client.logNote(txt);
                    if (webSocketLog.hasAttribute('onclick-note'))
                        eval(webSocketLog.getAttribute('onclick-note'));
                }
            }, false);
            this.shadow.appendChild(this.noteLog);

            this.logStatus = document.createElement('span');
            this.logStatus.setAttribute('id', 'logStatus');
            this.logStatus.setAttribute('style', 'font-size: small');
            this.shadow.appendChild(this.logStatus);

        }

        setupLogging(client) {
            //To-Do access the object instead of global 
            //Not effective client object 
            var webSocketLog = this;
            console.log('[setupLogging] Acquire msgClient from global ', WebSocketUtils[this.name].msgClient);
            client = WebSocketUtils[this.name].msgClient;
            client.addEventListener('connected', function(event) {
                webSocketLog.enableLogging = true;
            }, false);
            client.addEventListener('logstatus', function(event) {

                var logging = !!event.detail.logIsOpen;
                var filename = event.detail.logFilename;
                var format = event.detail.logType;

                console.log('logging', logging, filename, format);

                if (logging) {
                    webSocketLog.actionLog.setAttribute('value', "Stop Log");
                    webSocketLog.logStatus.innerHTML = filename + " (" + format + ")";
                    console.log('webSocketLog start');
                } else {
                    webSocketLog.actionLog.setAttribute('value', "Start Log");
                    webSocketLog.logStatus.innerHTML = "";
                    console.log('webSocketLog stop');
                }

            }, false);

            client.addEventListener('disconnected', function(event) {
                webSocketLog.enableLogging = false;
            }, false);

            return client;

        }

        disconnectedCallback() {
            //
        }

        attributeChangedCallback(name, oldValue, newValue) {

            switch (name) {
                case 'msg-client':
                    this.client = this.setupLogging(newValue);
                    console.log('[webSocketLog] ', this.client);
                    break;
                default:
                    console.log('Not implemented changed for', name);
                    throw 'Not implemented changed for' + name
            }


        }


    });

    function setClient(name, client) {

        WebSocketUtils[name].msgClient = client;
        var query = 'msgsocket-connector[connect-name=' + name + ']'
        var ele = document.querySelector(query);
        if (ele !== null) {
            ele.setAttribute('msg-client', WebSocketUtils[name]);
        }
        query = 'msgsocket-logging[connect-name=' + name + ']'
        ele = document.querySelector(query);
        if (ele !== null) {
            ele.setAttribute('msg-client', WebSocketUtils[name]);
        }
    }

    WebSocketUtils.setClient = setClient;

}).call(this);