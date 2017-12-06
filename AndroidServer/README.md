# Design Notes

## Top Level Architecture
The app comprises two modules.  A main application nd MainActivity, where all of the UI and service startup occurs. And a message service which manages all of the connections, messages, and logging.  The latter was chosen so we can run in the background and easily re-use the service in other applications.

The service is where all the work happens.  A generic class hierarchy comprising IConnectionMgr and IConnection objects are the primary things the service operates on.  Connection managers listen for new connections, and connections provide an abstraction for each distinct client.  The main service starts everything up and registers callback interfaces with each connection manager for new connection and message events.  The service is responsible for routing messages to all other connections.  This allows us to add general purpose routing rules, and message handling at the top level.  

The design is perhaps a little awkward, as message events come from the connection manager instead of a connection.  This was done to allow us to leverage Selectors and keep the number of active threads to a minimum.  However if you working with a non-Selectable interface such as Bluetooth and you spawn multiple receiving threads you'll need to route eveything through your own connection manager to fit witin the architecture.

That said, where possible we have reduced the number of threads in the application code; using Selectors, and making callbacks on the caller's thread.  This makes the application easier to work with but may have performance impacts.  See the pontential performance improvements section below.

You must always assume the service is being called by multiple treads and protect it accordingly.

## TODO List
* Implement the Bluetooth connection manager
* Make sure app sleep and wake works ok
* Power optimizations
 

## Assumptions
The following assumptions have been made:
* NetworkHeader is the de-facto header for all clients.  If you need to work with a different header then do that translation
as part of your specific IConnection implementations.
* All headers MUST have an ID and payload length.  To support any protocol you can comprise the ID out of any bits your want.
They just need to be unique within the overall message space.  The length MUST be the number of payload bytes after the header.


# Adding a new MessageService API and intent handler

The message service as a message based API, that sends responses via braodcast intents.
These are the steps to follow when adding a new API and intent. Note that the current design
could be cleaned up and streamlined to establish a better pattern, however a large number
of APIs isn't anticipated so a lot of time wasn't spent designing something more elegant.

## New API
1. To MessageServiceServerAPI add a new message ID and request method.  Just follow the established pattern
2. In MsgServerService::MsgServerAPIHandler::handleMessage add a case for your new message

## New Intent Response
1. Add a new intent id at the top of MsgServerService
2. In the handleMessage method mentioned in step 2 above - send a broadcast intent with your response using the new intent id
3. In AppBroadcastReceiver.java add a case to handle the new intent

# Potential Performance Improvements
* All message recv and routing is done on the thread for the message receiver (connection).  And we lock the MainService (which is the router).  It may be more performant to quickly post messages to the service and let a separate handler thread route each message. The infrasructure is in place vis a vis a MessageHandler.
* Logging may take substantial time with all the JSON conversions etc . We could also put logging on it's own queue and thread.
* Little attention as paid to how message buffers are allocated and managed.  We may be able to optimize by using memory pools and other tecniques.
