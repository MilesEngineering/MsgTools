package msgtools.milesengineering.msgserver;

import android.app.Service;
import android.content.Intent;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Process;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.Hashtable;

import Network.Connect;
import Network.LogStatus;
import Network.MaskedSubscription;
import Network.PrivateSubscriptionList;
import Network.QueryLog;
import Network.StartLog;
import Network.StopLog;
import Network.SubscriptionList;
import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;
import msgtools.milesengineering.msgserver.connectionmgr.bluetooth.BluetoothConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.tcp.TCPConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.websocket.WebsocketConnectionMgr;

/**
 * The main MsgServerService class.  This sets up a service thread, manages incoming messages
 * for API requests, and broadcasts intents to interested clients for new and dropped connections.
 */
public class MsgServerService extends Service implements Handler.Callback, IConnectionMgrListener {
    private static final String TAG = MsgServerService.class.getSimpleName();

    //
    // Constants
    //
    public static final String INTENT_SEND_SERVERS = "msgtools.milesengineering.msgserver.MsgServerServiceSendServers";
    public static final String INTENT_SEND_CONNECTIONS = "msgtools.milesengineering.msgserver.MsgServerServiceSendConnection";
    public static final String INTENT_SEND_NEW_CONNECTION = "msgtools.milesengineering.msgserver.MsgServerServiceSendNewConnection";
    public static final String INTENT_SEND_CLOSED_CONNECTION = "msgtools.milesengineering.msgserver.MsgServerServiceSendClosedConnection";
    public static final String INTENT_SEND_LOGGING_STATUS = "msgtools.milesengineering.msgserver.MsgServerServiceSendLoggingStatus";

    private final static int TCP_PORT = 5678;
    private final static int WEBSOCKET_PORT = 5679;
    private final static int TIMER_INTERVAL = 1000; // ms for each RX/TX update
    public final static String LOG_DIRECTORY = "MessageServer";

    private final Object m_Lock = new Object();   // Sync object
    private Messenger m_MsgHandler;               // For external client binding
    private Handler m_MsgServerHandler;           // To pump messages on this service...

    //
    // Connection Managers which handle connections on various transports for us.  Treated
    // as Singletons by this class
    //
    private IConnectionMgr m_TCPConnectionMgr;
    private IConnectionMgr m_WebsocketConnectionMgr;
    private IConnectionMgr m_BluetoothConnectionMgr;

    private String m_ServersJSON = "";  // List of connection managers in JSON for when a client app asks

    // Keep a class local record of connections - you might be wondering why we don't just get a list
    // of connections from each manager.  Threadsafety is the simple answer.  Rather than making
    // repeated copies of collections from the managers to iterate on for each message it's
    // more performant to maintain a global list in the service.
    // This of course leads to potential synchronization issues which we have to handle.
    private Hashtable<IConnection,IConnection> m_Connections =
            new Hashtable<IConnection,IConnection>();

    // Timer properties used to post RX/TX updates
    private boolean m_MessageCountDirty = false;
    private Handler m_TimerHandler = new Handler();
    private Runnable m_TimerRunnable = new Runnable() {
        @Override
        public void run() {
            synchronized (m_Lock) {
                if (m_MessageCountDirty == true) {
                    sendConnectionsIntent();
                    m_MessageCountDirty = false;
                }
            }
            m_TimerHandler.postDelayed(this, TIMER_INTERVAL);
        }
    };

    // Message Logging
    private MessageLogger m_MsgLogger;

    /**
     * Private utility class that processes Messages from bound clients.  This is where our
     * MsgServerServiceAPI messages are processed.
     */
    private class MsgServerAPIHandler extends Handler {
        @Override
        public void handleMessage(Message msg) {
            synchronized (m_Lock) {
                switch (msg.what) {
                    case MsgServerServiceAPI.ID_REQUEST_SERVERS:
                        android.util.Log.d(TAG, "Servers Request Received");
                        sendServersIntent();
                        break;
                    case MsgServerServiceAPI.ID_REQUEST_CONNECTIONS:
                        android.util.Log.d(TAG, "Connections Request Received");
                        sendConnectionsIntent();
                        break;
                    case MsgServerServiceAPI.ID_REQUEST_START_LOGGING:
                        android.util.Log.d(TAG, "Start Logging Request");
                        try {
                            String json = (String) msg.obj;
                            JSONObject jsonObj = (JSONObject) new JSONTokener(json).nextValue();
                            startLogging(jsonObj.getString("filename"), jsonObj.getString("msgVersion"), null);
                        }
                        catch(JSONException je) {
                            broadcastLoggingStatusIntent(je.getMessage());
                        }
                        break;
                    case MsgServerServiceAPI.ID_REQUEST_STOP_LOGGING:
                        android.util.Log.d(TAG, "Stop Logging Request");
                        stopLogging(null);
                        break;
                    default:
                        android.util.Log.w(TAG, "Unknown message type received by MsgServer.");
                        super.handleMessage(msg);
                }
            }
        }
    }

    public MsgServerService() {
        super();
    }

    @Override
    public void onCreate() {
        android.util.Log.i(TAG, "onCreate()");
        Toast.makeText(this, "MsgServer Service Starting...", Toast.LENGTH_SHORT).show();

        // Create a new logger
        m_MsgLogger = new MessageLogger(LOG_DIRECTORY);

        // Setup a binding message handler for any client bind requests
        m_MsgHandler = new Messenger(new MsgServerAPIHandler());

        // Spin up our message handling thread and ConnectionManagers
        HandlerThread ht = new HandlerThread( "MsgServerServiceThread",
                Process.THREAD_PRIORITY_BACKGROUND);
        ht.start();

        Looper looper = ht.getLooper();
        m_MsgServerHandler = new Handler(looper, this);

        // Instantiate our connection managers.
        m_TCPConnectionMgr = new TCPConnectionMgr(new InetSocketAddress(TCP_PORT), this);
        m_TCPConnectionMgr.start();

        m_WebsocketConnectionMgr = new WebsocketConnectionMgr(new InetSocketAddress(WEBSOCKET_PORT), this);
        m_WebsocketConnectionMgr.start();

        m_BluetoothConnectionMgr = new BluetoothConnectionMgr(this, this);
        m_BluetoothConnectionMgr.start();

        // Build up a servers JSON list for when clients ask.  This is static for now since we
        // hard code the servers.  If we move to dynamic model you might want to maintain a list
        // and rebuild on the fly...
        buildServersJSON();

        // Kick off a 1 second timer which we will use to post RX/TX updates
        m_TimerHandler.postDelayed(m_TimerRunnable, TIMER_INTERVAL);
    }

    @Override
    public void onDestroy() {
        android.util.Log.i(TAG, "onDestroy()");
        Toast.makeText(this, "MsgServer Service Being Destroyed...", Toast.LENGTH_SHORT).show();

        m_MsgLogger.stopLogging();

        m_TCPConnectionMgr.requestHalt();
        m_MsgServerHandler.getLooper().quitSafely();

        m_TCPConnectionMgr = null;
        m_MsgServerHandler = null;

        m_MsgServerHandler.getLooper().quitSafely();

        m_TimerHandler.removeCallbacks(m_TimerRunnable);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        android.util.Log.i(TAG, "onStartCommand(...)");

        if (flags == START_FLAG_REDELIVERY) {
            return START_NOT_STICKY;
        }

        return START_STICKY;
    }

    //
    // Service binding stuff...
    //

    @Override
    public IBinder onBind(Intent intent) {
        android.util.Log.i(TAG, "onBind(...)");
        return m_MsgHandler.getBinder();
    }

    @Override
    public void onRebind(Intent intent) {
        android.util.Log.i(TAG, "onRebind(...)");
        // TODO: reset any state based on binding if needed
    }

    @Override
    public boolean onUnbind(Intent intent) {
        android.util.Log.i(TAG, "onUnbind(...)");
        return super.onUnbind(intent);
    }

    /**
     * Process messages from bound clients...
     * @param msg message to process
     * @return always returns false to continue processing.
     */
    @Override
    public boolean handleMessage(Message msg) {
        android.util.Log.i(TAG, "MessageHandler::handleMessage(...)");

        // This is where we process messages from our bound clients
        switch(msg.what) {
            default:
                android.util.Log.w(TAG, "Received unknown message: " + msg.what);
        }

        return false;   // Keep going
    }

    //
    // Connection Manager Listener
    //

    @Override
    public void onNewConnection(IConnectionMgr mgr, IConnection newConnection) {
        synchronized (m_Lock) {
            if (m_Connections.put(newConnection, newConnection) == null) {
                broadcastNewConnectionIntent(mgr, newConnection);
            } else {
                android.util.Log.w(TAG, "Received a duplicate new connection event");
            }
        }

    }

    @Override
    public void onClosedConnection(IConnectionMgr mgr, IConnection closedConnection) {
        synchronized (m_Lock) {
            if ( m_Connections.remove(closedConnection) == null ) {
                android.util.Log.w(TAG, "Attempted to remove a closed connection that is not being tracked");
            }
            else
                broadcastClosedConnectionIntent(mgr, closedConnection);
        }
    }

    @Override
    public void onMessage(IConnectionMgr mgr, IConnection srcConnection, NetworkHeader networkHeader,
                          ByteBuffer hdrBuff, ByteBuffer payloadBuff) {
        synchronized (m_Lock) {

            // If we don't know about this connection then flag a warning (probably a mgr bug)
            // and add it to our local list.
            if ( m_Connections.containsKey(srcConnection) == false ) {
                android.util.Log.w(TAG, "Received message from unknown connection.");
                m_Connections.put(srcConnection, srcConnection);
                broadcastNewConnectionIntent(mgr, srcConnection);
            }

            // Check to see if this is a special purpose message (Start/Stop Log, LogStatus, etc)
            // and handle the message as appropriate.  Don't route these messages out
            int msgId = networkHeader.GetMessageID();
            switch( msgId ) {
                case StartLog.MSG_ID:
                    StartLog msg = new StartLog(hdrBuff, payloadBuff);
                    StringBuilder sb = new StringBuilder();

                    for(int i = 0; i < StartLog.LogFileNameFieldInfo.count; i++) {
                        char nextChar = (char)msg.GetLogFileName(i);
                        if ( nextChar != 0x0 )
                            sb.append( nextChar );
                        else
                            break;
                    }

                    String logFilename = sb.toString();

                    if ( logFilename.length() > 0)
                        startLogging( logFilename, "", srcConnection );

                    break;

                case StopLog.MSG_ID:
                    stopLogging(srcConnection);
                    break;

                case QueryLog.MSG_ID:
                    sendLogStatus(srcConnection);
                    break;

                case LogStatus.MSG_ID:
                case Connect.MSG_ID:
                case MaskedSubscription.MSG_ID:
                case SubscriptionList.MSG_ID:
                case PrivateSubscriptionList.MSG_ID:
                    // Unsupported at present
                    break;
                default:
                    android.util.Log.d(TAG, String.format("SEQUENCE=%d", (short)(0x000000FF & payloadBuff.get(0))));
                    routeMessage(srcConnection, networkHeader, hdrBuff, payloadBuff);
                    m_MsgLogger.log(hdrBuff, payloadBuff);
            }

            // Next time our timer fires post a RX/TX update to everyone
            m_MessageCountDirty = true;
        }
    }

    private void routeMessage(IConnection srcConnection, NetworkHeader networkHeader, ByteBuffer hdrBuff, ByteBuffer payloadBuff) {
        for(IConnection c : m_Connections.values()) {
            try {
                // Don't echo messages back to the sender
                if (c != srcConnection && c.sendMessage(networkHeader, hdrBuff,
                        payloadBuff) == false) {
                    android.util.Log.w(TAG, "Message not sent by connection: " +
                            c.getDescription());
                }
            }
            catch(Exception e) {
                android.util.Log.w(TAG, "Exception sending message on connection: " +
                        c.getDescription());
                android.util.Log.w(TAG, e.toString());
            }
        }
    }

    private void sendLogStatus(IConnection destination) {
        LogStatus status = new LogStatus();

        if ( m_MsgLogger.isEnabled() == true ) {
            status.SetLogOpen( (short)1 );

            byte[] logFilename = m_MsgLogger.getFilename().getBytes();
            for (int i = 0; i < logFilename.length; i++)
                status.SetLogFileName(logFilename[i], i);
            status.SetLogFileType((short) LogStatus.LogFileTypes.Binary.intValue());
        }
        else
            status.SetLogOpen( (short)0 );

            destination.sendMessage( status.GetHeader(), status.GetHeader().GetBuffer(), status.GetBuffer() );
    }

    //
    // MsgServerServiceAPI Handlers
    //

    private void sendServersIntent() {
        Intent sendIntent = new Intent();
        sendIntent.setAction(MsgServerService.INTENT_SEND_SERVERS);
        sendIntent.putExtra(Intent.EXTRA_TEXT, m_ServersJSON);

        sendBroadcast(sendIntent);
    }

    private void sendConnectionsIntent() {
        // Build up a full list of connections...going to again do brute force JSON
        // conversion. Build up a list of connections...
        JSONArray jarray = new JSONArray();
        for( IConnection c : m_Connections.values() ) {
            jarray.put(getConnectionJSON(c));
        }

        // Broadcast the list
        Intent sendIntent = new Intent();
        sendIntent.setAction(MsgServerService.INTENT_SEND_CONNECTIONS);
        sendIntent.putExtra(Intent.EXTRA_TEXT, jarray.toString());

        sendBroadcast(sendIntent);
    }

    private void startLogging(String filename, String msgVersion, IConnection srcConnection) {
        String errorMsg = m_MsgLogger.startLogging(filename, msgVersion);
        broadcastLoggingStatusIntent(errorMsg);

        // If our log request came from a remote client, echo our new status to confirm...
        if ( srcConnection != null )
            sendLogStatus(srcConnection);
    }

    private void stopLogging(IConnection srcConnection) {
        String errorMsg = m_MsgLogger.stopLogging();
        broadcastLoggingStatusIntent(errorMsg);

        // If our log request came from a remote client, echo our new status to confirm...
        if ( srcConnection != null )
            sendLogStatus(srcConnection);
    }

    //
    // Misc utility methods
    //

    private void buildServersJSON() {
        // Brute force method here - nothing fancy
        IConnectionMgr[] managers = new IConnectionMgr[3];
        managers[0] = m_BluetoothConnectionMgr;
        managers[1] = m_TCPConnectionMgr;
        managers[2] = m_WebsocketConnectionMgr;

        JSONArray jarray = new JSONArray();
        for( IConnectionMgr cm : managers ) {
            Hashtable<String,String> map = new Hashtable<String,String>();
            map.put("protocol", cm.getProtocol());
            map.put("description", cm.getDescription());

            jarray.put(JSONObject.wrap(map));
        }

        m_ServersJSON = jarray.toString();
    }

    private JSONObject getConnectionJSON(IConnection conn) {
        // TODO: Probably ought to create a utility class for this so clients
        // can stay in sync...
        JSONObject jsonObj = new JSONObject();
        try {
            jsonObj.put("id", conn.hashCode());
            jsonObj.put("description", conn.getDescription());
            jsonObj.put("recvCount", conn.getMessagesReceived());
            jsonObj.put("sendCount", conn.getMessagesSent());
            jsonObj.put("protocol", conn.getProtocol());
        }
        catch( JSONException je ) {
            je.printStackTrace();
        }

        return jsonObj;
    }

    //
    // Broadcast Intent methods - our reverse API of sorts...
    //

    private void broadcastNewConnectionIntent(IConnectionMgr mgr, IConnection newConnection) {
        android.util.Log.i(TAG, "broadcastNewConnectionIntent");
        broadcastConnectionChangedIntent(MsgServerService.INTENT_SEND_NEW_CONNECTION,
                mgr, newConnection);
    }

    private void broadcastClosedConnectionIntent(IConnectionMgr mgr, IConnection closedConnection) {
        android.util.Log.i(TAG, "broadcastClosedConnectionIntent");
        broadcastConnectionChangedIntent(MsgServerService.INTENT_SEND_CLOSED_CONNECTION,
                mgr, closedConnection);
    }

    private void broadcastConnectionChangedIntent(String action, IConnectionMgr mgr,
                                                  IConnection connection) {
        android.util.Log.d(TAG, "broadcastConnectionChangedIntent");

        JSONObject jsonObject = getConnectionJSON(connection);

        // Broadcast the list
        Intent sendIntent = new Intent();
        sendIntent.setAction(action);
        sendIntent.putExtra(Intent.EXTRA_TEXT, jsonObject.toString());

        sendBroadcast(sendIntent);
    }
    private void broadcastLoggingStatusIntent(String error) {
        android.util.Log.d(TAG, "broadcastLoggingStatusIntent");

        JSONObject jsonObj = new JSONObject();
        try {
            jsonObj.put("enabled", m_MsgLogger.isEnabled());
            if (m_MsgLogger.isEnabled() == true) {
                if ( m_MsgLogger.getFilename() != null )
                    jsonObj.put("filename", m_MsgLogger.getFilename());

                if ( m_MsgLogger.getMsgVersion() != null )
                    jsonObj.put("msgVersion", m_MsgLogger.getMsgVersion());
            }

            if (error != null)
                jsonObj.put("error", error);
        }
        catch( JSONException je ) {
            // Should never happen.
            je.printStackTrace();
        }

        Intent sendIntent = new Intent();
        sendIntent.setAction(INTENT_SEND_LOGGING_STATUS);
        sendIntent.putExtra(Intent.EXTRA_TEXT, jsonObj.toString());

        sendBroadcast(sendIntent);
    }
}
