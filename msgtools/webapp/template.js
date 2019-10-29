var msgclient = null

//
// Bare bones setup of message tools
//
function initMsgTools() {
    // Initialize MsgTools itself...
    msgtools.setMsgDirectory('{{webdir}}')
        .then(() => {
            // Load app specific messages
            msgtools.loadMessages({{ messages }})
                .then(() => {
                    // Once all scripts have loaded then we can
                    // instantiate a connection to the server...
                    connectToServer()
                })
                .catch(error => {
                    // TODO: Any specific error handling you want here
                    console.log(error)
                })
        })
        .catch(error => {
            // TODO: Any specific error handling you want here
            console.log(error)
        })
}

//
// Call only after all messages have been loaded.
// This instantiates a new connection to the server
//
function connectToServer() {
    msgclient = new msgtools.MessagingClient('{{appname}}', window);
    //Assign client to use msgsocket-connector and msgsocket-logging widgets
    {% if widgets %} WebSocketUtils.setClient('{{appname}}', msgclient); {% endif %}

    msgclient.addEventListener('connected', () => {
        console.log('Connected')
        // TODO: Any custom handling needed
    })
    msgclient.addEventListener('message', (event) => {
        console.log('New Message')

        // OPTiONAL: Pretty print the message to the console
        console.log(msgtools.toJSON(event.detail.message));
        console.log(msgtools.prettyPrint(event.detail.message));

        // TODO: Any custom handling needed
    })
    msgclient.addEventListener('disconnected', () => {
        console.log('Disconnected')

        // TODO: Any custom handling needed
    })
    msgclient.addEventListener('error', () => {
        console.log('Error')

        // TODO: Any custom handling needed
    })
    msgclient.addEventListener('logstatus', (event) => {
        console.log('LogStatus')

        // TODO: Any custom handling needed
    })

    {% if not widgets %}
        // Uncomment and modify to exercise option values below
        // indicate msgtools defaults for use with local insecure 
        // connections.  We assume the target server is MsgServer
        // and we emit Connect and other messages expected by that
        // server as part of our connection sequence.
        var options = new Map()
        //options.set('secureSocket', false)
        //options.set('server', '127.0.0.1')
        //options.set('port', 5679)
        //options.set('subscriptionMask', 0x00000000)
        //options.set('subscriptionValue', 0x0000000)
        //options.set('suppressConnect', false)
        //options.set('suppressMaskedSubscription', false)
        //options.set('suppressQueryLog', false)
        msgclient.connect(options)
    {% endif %}
}
