
class WebConsole extends msgtools.MessagingClient {
    constructor() {
        super('WebConsole', window);
    }
    onconnected() {
        console.log('Connected')
    }
    onmessage(msg) {
        console.log('New Message')
        console.log(msgtools.toJSON(msg))
        console.log(reflectionExampleFn(msg))
    }
    ondisconnected() {
        console.log('Disconnected')
    }
    onerror(errorEvent) {
        console.log('Error: ' + errorEvent)
    }
}

function connectToServer() {
    var client = new WebConsole()

    var options = new Map()
    //options.set('secureSocket', true)
    //options.set('server', localhost)
    //options.set('port', 5678)
    //options.set('subscriptionMask', 0x00000001)
    //options.set('subscriptionValue', 0xFFFF4080)
    //options.set('suppressConnect', true)
    //options.set('suppressMaskedSubscription', true)
    //options.set('suppressQueryLog', true)
    client.connect(options)

}

//  this is an example of how to iterate over the fields of a message, getting metadata about each field
// (and bitfield), and getting the value of the field using the get function called with bracket notation obj[fnName](), instead of obj.fn()
function reflectionExampleFn(obj) {
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