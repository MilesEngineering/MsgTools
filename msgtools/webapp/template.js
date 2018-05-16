//
// Bare bones setup of message tools
//
function initMsgTools() {
    // Initialize MsgTools itself...
    msgtools.setMsgDirectory('{{webdir}}')
        .then(()=>{
            // Load app specific messages
            msgtools.loadMessages({{messages}})
                .then(()=>{
                    // Once all scripts have loaded then we can 
                    // instantiate a connection to the server...
                    connectToServer()
                })
                .catch(error=>{
                    // TODO: Any specific error handling you want here
                    console.log(error)
                })
        })
        .catch(error=>{
            // TODO: Any specific error handling you want here
            console.log(error)
        })
}

//
// Call only after all messages have been loaded.
// This instantiates a new connection to the server
//
function connectToServer() {
    var client = new msgtools.MessagingClient('{{appname}}', window)
    client.addEventListener('connected', ()=>{
        console.log('Connected')
        // TODO: Any custom handling needed
    })
    client.addEventListener('message', (event)=>{
        console.log('New Message')

        // OPTiONAL: Pretty print the message to the console
        console.log(msgtools.toJSON(event.detail.message));
        console.log(prettyPrint(event.detail.message));

        // TODO: Any custom handling needed
    })
    client.addEventListener('disconnected', ()=>{
        console.log('Disconnected')

       // TODO: Any custom handling needed
    })
    client.addEventListener('error', ()=>{
        console.log('Error')

    // TODO: Any custom handling needed
    })
    client.addEventListener('logstatus', (event)=>{
        console.log('LogStatus')
        
        // TODO: Any custom handling needed
    })

    // Uncomment and modify to exercise option values below
    // indicate msgtools defaults for use with local insecure 
    // connections.  We assume the taget server is MsgServer
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
    client.connect(options)
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