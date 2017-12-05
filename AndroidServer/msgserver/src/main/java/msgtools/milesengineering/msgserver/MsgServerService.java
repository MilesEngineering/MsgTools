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

import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Hashtable;

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

    public static final String INTENT_SEND_SERVERS = "msgtools.milesengineering.msgserver.MsgServerServiceSendServers";
    public static final String INTENT_SEND_CONNECTIONS = "msgtools.milesengineering.msgserver.MsgServerServiceSendConnection";
    public static final String INTENT_SEND_NEW_CONNECTION = "msgtools.milesengineering.msgserver.MsgServerServiceSendNewConnection";
    public static final String INTENT_SEND_CLOSED_CONNECTION = "msgtools.milesengineering.msgserver.MsgServerServiceSendClosedConnection";

    private final static int TCP_PORT = 5678;
    private final static int WEBSOCKET_PORT = 5679;

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

        m_BluetoothConnectionMgr = new BluetoothConnectionMgr(this, null);
        m_BluetoothConnectionMgr.start();

        // Build up a servers JSON list for when clients ask.  This is static for now since we
        // hard code the servers.  If we move to dynamic model you might want to maintain a list
        // and rebuild on the fly...
        buildServersJSON();
    }

    @Override
    public void onDestroy() {
        android.util.Log.i(TAG, "onDestroy()");
        Toast.makeText(this, "MsgServer Service Being Destroyed...", Toast.LENGTH_SHORT).show();

        // TODO: Stop our message handling loop and close all connections etc.
        m_TCPConnectionMgr.requestHalt();
        m_MsgServerHandler.getLooper().quitSafely();

        m_TCPConnectionMgr = null;
        m_MsgServerHandler = null;
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
                broadcastClosedConnectionIntent(mgr, closedConnection);
            }
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
            }

            for(IConnection c : m_Connections.values()) {
                try {
                    // Don't echo messages back to the sender
                    if (c != srcConnection && c.sendMessage(networkHeader, hdrBuff,
                            payloadBuff) == false) {
                        // TODO: When we have  a friendly connection name log it here
                        android.util.Log.w(TAG, "Message not sent by connection: ");
                    }
                }
                catch(Exception e) {
                    // TODO: When we have  a friendly connection name log it here
                    android.util.Log.w(TAG, "Exception sending message on connection: ");
                    android.util.Log.w(TAG, e.toString());
                }
            }

            // TODO: Generate an intent for interested parties
        }
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
            map.put("protocol", cm.protocol());
            map.put("description", cm.description());

            jarray.put(JSONObject.wrap(map));
        }

        m_ServersJSON = jarray.toString();
    }

    private JSONObject getConnectionJSON(IConnection conn) {
        // TODO: Probably ought to create a utility class for this so clients
        // can stay in sync...
        Hashtable<String,String> map = new Hashtable<>();
        map.put("id", Integer.toString(conn.hashCode()));
        map.put("description", conn.getDescription());
        map.put("recvCount", Integer.toString(conn.getMessagesReceived()));
        map.put("sentCount", Integer.toString(conn.getMessagesSent()));

        return (JSONObject)JSONObject.wrap(map);
    }

    //
    // Broadcast Intent methods
    //

    private void broadcastNewConnectionIntent(IConnectionMgr mgr, IConnection newConnection) {
        android.util.Log.i(TAG, "broadcastNewConnectionIntent");
        broadcastConnectionChangedIntent(MsgServerService.INTENT_SEND_NEW_CONNECTION,
                mgr, newConnection);
    }

    private void broadcastClosedConnectionIntent(IConnectionMgr mgr, IConnection newConnection) {
        android.util.Log.i(TAG, "broadcastNewConnectionIntent");
        broadcastConnectionChangedIntent(MsgServerService.INTENT_SEND_CLOSED_CONNECTION,
                mgr, newConnection);
    }

    private void broadcastConnectionChangedIntent(String action, IConnectionMgr mgr,
                                                  IConnection connection) {
        android.util.Log.d(TAG, "broadcastConnectionChangedIntent");

        try {
            JSONObject jsonObject = getConnectionJSON(connection);
            jsonObject.put("protocol", mgr.protocol());

            // Broadcast the list
            Intent sendIntent = new Intent();
            sendIntent.setAction(action);
            sendIntent.putExtra(Intent.EXTRA_TEXT, jsonObject.toString());

            sendBroadcast(sendIntent);
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }
}
