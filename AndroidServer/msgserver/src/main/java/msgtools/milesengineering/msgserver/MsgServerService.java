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

import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.Hashtable;

import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;
import msgtools.milesengineering.msgserver.connectionmgr.tcp.TCPConnectionMgr;

/**
 * The main MsgServerService class.  This sets up a service thread, manages incoming messages
 * for API requests, and broadcasts intents to interested clients for new and dropped connections.
 */
public class MsgServerService extends Service implements Handler.Callback, IConnectionMgrListener {
    private static final String TAG = MsgServerService.class.getSimpleName();

    public static final String INTENT_ACTION = "msgtools.milesengineering.msgserver.MsgServerServiceAction";
    private final static int TCP_PORT = 5678;

    private final Object m_Lock = new Object();   // Sync object
    private Messenger m_MsgHandler; // For external client binding
    private Handler m_MsgServerHandler; // To pump messages on this service...

    //
    // Connection Managers which handle connections on various transports for us.  Treated
    // as Singletons by this class
    //
    private IConnectionMgr m_TCPConnectionMgr;

    // Keep a class local record of connections - you might be wondering why we don't just get a list
    // of connections from each manager.  Threadsafety is the simple answer.  Rather than making
    // repeated copies of collections from the managers to iterate on for each message it's
    // more performant to maintain a global list in the service.
    // This of course leads to potential synchronization issues which we have to handle.
    private Hashtable<IConnection,IConnection> m_Connections =
            new Hashtable<IConnection,IConnection>();


    /**
     * Private utility class that processes Messages from bound clients
     */
    private class MsgServerAPIHandler extends Handler {
        @Override
        public void handleMessage(Message msg) {
            switch(msg.what) {
                default:
                    android.util.Log.w(TAG, "Unknown message type received by MsgServer.");
                    super.handleMessage(msg);
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

        // MODEBUG: Send a broadcast event to test App receipt
        Intent sendIntent = new Intent();
        sendIntent.setAction(MsgServerService.INTENT_ACTION);
        sendIntent.putExtra(Intent.EXTRA_TEXT, "TEST SERVER");

        sendBroadcast(sendIntent);

        // MODEBUG: Send a message to test our message loop
        Message msg = m_MsgServerHandler.obtainMessage();
        msg.arg1 = startId;
        m_MsgServerHandler.sendMessage(msg);

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

        // Normally we would do some work here, like download a file.
        // For our sample, we just sleep for 5 seconds.
        try {
            // TODO: Insert message handling here - sleep for now
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            // Restore interrupt status.
            Thread.currentThread().interrupt();
        }

        return false;   // Keep going
    }

    //
    // Connection Manager Listener
    //

    @Override
    public void onNewConnection(BaseConnectionMgr mgr, IConnection newConnection) {
        synchronized (m_Lock) {
            if (m_Connections.put(newConnection, newConnection) == null) {
                // TODO: Generate an intent for interested parties...
            } else {
                android.util.Log.w(TAG, "Received a duplicate new connection event");
            }
        }

    }

    @Override
    public void onClosedConnection(BaseConnectionMgr mgr, IConnection closedConnection) {
        synchronized (m_Lock) {
            if ( m_Connections.remove(closedConnection) == null ) {
                android.util.Log.w(TAG, "Attempted to remove a closed connection that is not being tracked");
                // TODO: Generate an intent for interested parties
            }
        }

    }

    @Override
    public void onMessage(BaseConnectionMgr mgr, IConnection srcConnection,
                          long msgId, ByteBuffer payload) {
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
                    if (c != srcConnection && c.sendMessage(msgId, payload) == false) {
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


}
