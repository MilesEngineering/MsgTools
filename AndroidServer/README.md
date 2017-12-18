# Getting Started
The app requires some setup before you can run it, however the overall steps for setup are simple.

1. Pull MsgTools down from the repo
2. From the root directory of MsgTools type _make test_.  This will generate a set of base headers the app relies on to determine the payload length
   of a message and properly read and route it.  See the Customizing for your own messages below for more details on how you configure the app to use
   your own messages.
3. Fire up Android studio and build.  You may need to download appropriate SDKs and build tools, but there is otherwise nothing special.

Note: There are some code generator bugs in MsgTools.  You can get around these by deleting all the test case and taxonomy messages (both the Taxonomy directory, and the TaxonomyHeader in the headers folder) in your test obj directory.

# Customizing the App for your own Messages
Normally you will define your own YAML specifications and generate your own messages and code.  The app is designed to be completely agnostic to everything
except the headers.  NetworkHeader and BluetoothHeader must both be defined, and expose a GetDataLength() function and SIZE property.  MsgTools will generally
do this for you.  You just need to define the appropriate headers for your protocol.

Once you have setup your own fork go into msgserver's build.gradle file and update the source directories to include your generated source.  See that file for
further comments.

If you modify the app to expect other specific messages be sure to add appropriate YAML to the parser/test directory.

# Design Notes

## Top Level Architecture
The app comprises two modules.  A main application with a MainActivity, where all of the UI and service startup occurs. And a message service which manages all of the connections, messages, and logging.  The latter was chosen so we can run in the background and easily re-use the service in other applications.

The service is where all the work happens.  A generic class hierarchy comprising IConnectionMgr and IConnection objects are the primary things the service operates on.  Connection managers listen for new connections, and connections provide an abstraction for each distinct client.  The main service starts everything up and registers callback interfaces with each connection manager for new connection and message events.  The service is responsible for routing messages to all other connections.  This allows us to add general purpose routing rules, and message handling at the top level.  

The design is perhaps a little awkward, as message events come from the connection manager instead of a connection.  This was done to allow us to leverage Selectors and keep the number of active threads to a minimum.  However if you working with a non-Selectable interface, such as Bluetooth, and you spawn multiple receiving threads you'll need to route new message events through your own connection manager (or share the helper class) to fit witin the architecture.  If you share, be sure to use a weak reference to avoid memory leaks.

That said, where possible we have reduced the number of threads in the application code; using Selectors, and making callbacks on the caller's thread.  This makes the application easier to work with but may have performance impacts.  See the pontential performance improvements section below.

You must always assume the service is being called by multiple treads and protect it accordingly.

## TODO List
* Improve the Gradle setup to point the app at your own version of MsgTools/MsgApp and generated code.
* Performance evaluation - the app basically tries to be single threaded right now.  Strong doubt performance is stellar as a result...
* Add Bluetooth broadcast intent handlers for the following cases and improve overall connectivity algorithm.  Right now it's brute force attempt to connect to whatever bonded devices we have:
    * ACTION_BOND_STATE_CHANGED -> Attempt to connect if just bonded
    * ACTION_STATE_CHANGED -> Attempt to connect to bonded devices
* Add support for reconnect (enabled/disabled, device drops, etc)
* Add remote start/stop logging handling
* Stop the service when done.  Need to figure out what done means.  Could be when the last app/client unbinds.  Could be when the last connection is dropped.  Could be...???
* Make sure app sleep and wake works ok - did some prelim testing and it seems ok
* Power optimizations (see next item for a major one, but there are sure to be others)
* Look into better ways to detect and correct lost TCP connections.  It would appear the Selector thread automatically selects when the connection is lost 
  (meaning you disconnect the client - such as MsgScope) so that you get into a tight loop repeatedly reading 0 bytes.  Which of course pegs the CPU and drains
  your battery in short order.  The best thing might be a hard line policy of closing any connection that returns 0 bytes on a read select.  Not yet sure that's the best
  route though.
* Make a more elegant intent broadcast "API" handler to make it more clear about the intents and payloads involved.  The code around this is a little messy.
* See about using reflection to automatically assign identically named fields from/to a NetworkHeader and BluetoothHeader.
 

## Assumptions
The following assumptions have been made:
* NetworkHeader is the de-facto header for all clients.  If you need to work with a different header then do that translation
as part of your specific IConnection implementations.
* All headers MUST have an GetDataLength() and SIZE.  The length MUST be the number of payload bytes after the header.
* All NetworkHeaders MUST  have a Time field.  The app stuff ms since server startup into this field on Bluetooth messages.  It otherwise leaves this field alone assuming the sender set the Time.


# Adding a new MessageService API and intent handler

The message service is a message based API, that sends responses via braodcast intents.
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
* Logging may take substantial time with all the JSON conversions etc. We could also put logging on it's own queue and thread to avoid blocking the message send/recv code.
* Little attention was paid to how message buffers are allocated and managed.  We may be able to optimize by using memory pools and other techniques.
