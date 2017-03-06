// this prints the whole message dictionary
//console.log(MessageDictionary);

// create a connection
var msgSocket = new MessagingClient();

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

// this is the callback to handle received messages
msgSocket.onmsg = function(msg)
{
    // this writes the JSON of the message's header
    //console.log(toJSON(msg.hdr));
    console.log(toJSON(msg));
    console.log(reflectionExampleFn(msg));
    // this gets the javascript object from a message, instead of accessing the fields using get/set
    //msg.toObject();
};

// this is the callback to do stuff after the connection is made
msgSocket.onconnect = function()
{
};
