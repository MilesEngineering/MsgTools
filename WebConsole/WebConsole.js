// this prints the whole message dictionary
//console.log(MessageDictionary);

// create a connection
var msgSocket = new MessagingClient();

// this is the callback to handle received messages
msgSocket.onmsg = function(msg)
{
    // this writes the JSON of the message's header
    //console.log(toJSON(msg.hdr));
    console.log(toJSON(msg));
    // this gets the javascript object from a message, instead of accessing the fields using get/set
    //msg.toObject();
};

// this is the callback to do stuff after the connection is made
msgSocket.onconnect = function()
{
};
