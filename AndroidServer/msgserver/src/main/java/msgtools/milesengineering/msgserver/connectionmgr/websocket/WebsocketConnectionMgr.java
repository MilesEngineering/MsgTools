package msgtools.milesengineering.msgserver.connectionmgr.websocket;

import android.net.Network;

import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.util.Hashtable;

import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.ConnectionListenerHelper;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;
import msgtools.milesengineering.msgserver.connectionmgr.utils;

/**
 * ConnectionMgr implementation for handling Websocket connections. We're basically
 * wrapping the org.java-websocket package into a standard interface for our service.
 */
public class WebsocketConnectionMgr extends WebSocketServer implements IConnectionMgr {
    private static final String TAG = WebsocketConnectionMgr.class.getSimpleName();
    private final Object m_Lock = new Object();

    private Hashtable<WebSocket, WebsocketConnection> m_Connections =
            new Hashtable<WebSocket, WebsocketConnection>();
    private ConnectionListenerHelper m_Listeners;
    private boolean m_HaltPending;
    private InetSocketAddress m_SocketAddress;

    public WebsocketConnectionMgr(InetSocketAddress addr, IConnectionMgrListener listener ) {
        super(addr);
        android.util.Log.i(TAG, "WebsocketConnectionMgr(...)");
        m_SocketAddress = addr;
        this.setReuseAddr(true);

        m_Listeners = new ConnectionListenerHelper(TAG, this);
        addListener(listener);
    }

    /**
     * Private implementation of our underlying websocket connection.
     */
    private class WebsocketConnection implements IConnection {
        private final Object m_Lock = new Object(); // Sync object
        private WeakReference<WebSocket> m_Websocket;
        private int m_SentCount = 0;
        private int m_ReceivedCount = 0;

        /**
         * Ctor
         * @param ws Websocket we're wrapping and associated with
         */
        public WebsocketConnection(WebSocket ws) {
            m_Websocket = new WeakReference<WebSocket>(ws);
        }

        public void incrementReceived() {
            m_ReceivedCount++;
        }

        //
        // IConnection methods
        //
        @Override
        public boolean sendMessage(NetworkHeader networkHeader, ByteBuffer hdrBuff,
                                   ByteBuffer payloadBuff) {
            boolean retVal = false;
            synchronized (m_Lock) {
                if (m_Websocket != null) {
                    try {
                        WebSocket ws = m_Websocket.get();

                        // We need to be sure to send one buffer to properly frame the Websocket
                        // message for parsing on the other side.  So pack the hdr and payload
                        // into one buffer.  It is a perfectly valid case to have a null payload.
                        // So be sure to check and handle that!
                        int totalLength = hdrBuff.limit() + (payloadBuff == null ? 0 :
                                payloadBuff.limit());

                        ByteBuffer sendBuf = ByteBuffer.allocate(totalLength);

                        hdrBuff.position(0);
                        sendBuf.put(hdrBuff);

                        if (payloadBuff != null ) {
                            payloadBuff.position(0);
                            sendBuf.put(payloadBuff);
                        }

                        sendBuf.position(0);
                        ws.send(sendBuf);

                        m_SentCount++;
                        retVal = true;
                    }
                    catch(Exception e) {
                        android.util.Log.w(TAG, "Exception sending Websocket ms");
                        android.util.Log.w(TAG, e.toString());
                    }
                }
            }

            return retVal;
        }

        @Override
        public String getDescription() {
            String retVal = "Unknown client";
            WebSocket ws = m_Websocket.get();

            if ( ws != null ) {
                InetSocketAddress addr = ws.getRemoteSocketAddress();
                if ( addr != null )
                    retVal = addr.toString().substring(1);
            }

            return retVal;
        }

        @Override
        public String getProtocol() { return "WS"; }

        @Override
        public int getMessagesSent() {
            return m_SentCount;
        }

        @Override
        public int getMessagesReceived() {
            return m_ReceivedCount;
        }

        @Override
        public void close() throws IOException {
            synchronized(m_Lock) {
                if (m_Websocket != null) {
                    m_Websocket.get().close();
                    m_Websocket = null;
                }
            }
        }
    }

    //
    // IConnectionMgr Methods
    //
    @Override
    public void addListener(IConnectionMgrListener listener) {
        synchronized (m_Lock) {
            m_Listeners.addListener(listener);
        }
    }

    @Override
    public boolean removeListener(IConnectionMgrListener listener) {
        synchronized (m_Lock) {
            return m_Listeners.removeListener(listener);
        }
    }

    @Override
    public void requestHalt() {
        synchronized (m_Lock) {
            try {
                // This will also clean up all open connections so we don't need
                // to worry about that...
                stop();
            }
            catch(Exception ie) {
                android.util.Log.w(TAG, "Exception stopping WebsocketConnectionMgr");
                android.util.Log.w(TAG, ie.toString());
            }

            m_HaltPending = true;
        }
    }

    @Override
    public boolean haltPending() {
        return m_HaltPending;
    }

    @Override
    public String getProtocol() { return "WS"; }

    @Override
    public String getDescription() {
        String retVal = "Not Listening";
        if ( m_SocketAddress != null ) {
            InetAddress ia = utils.getHostAddress();
            retVal = ia.toString() + ":" + m_SocketAddress.getPort();
        }

        return retVal.substring(1);
    }

    //
    // WebSocketServerMethods
    //
    @Override
    public void onOpen(WebSocket conn, ClientHandshake handshake) {
        synchronized (m_Lock) {
            // Create a new IConnection object to track our app specific
            // stuff and add it to our active connections list.
            WebsocketConnection wc = new WebsocketConnection(conn);

            // Make sure we're tracking the connection for message handling later...
            m_Connections.put(conn,wc);

            m_Listeners.onNewConnection(wc);
        }
    }

    @Override
    public void onClose(WebSocket conn, int code, String reason, boolean remote) {
        synchronized (m_Lock) {
            // Remove from our local list of tracked connections
            WebsocketConnection wsc = m_Connections.remove(conn);
            if ( wsc != null ) {
                m_Listeners.onClosedConnection(wsc);
            } else {
                android.util.Log.w(TAG, "Received closed event but we aren't tracking this connection!");
            }

        }
    }


    @Override
    public void onMessage(WebSocket conn, String message) {
        ByteBuffer msgWrapper = ByteBuffer.wrap(message.getBytes());
        onMessage(conn, msgWrapper);
    }

    @Override
    public void onMessage(WebSocket conn, ByteBuffer msg) {
        synchronized (m_Lock) {

            // Get our connection mgr IConnection implementation...
            WebsocketConnection wsc = m_Connections.get(conn);
            if ( wsc != null ) {

                // Make sure we have enough data to work with...
                if (msg.capacity() >= NetworkHeader.SIZE) {
                    msg.position(0);

                    // We need to parse out the message ID and payload...
                    byte[] hdrBytes = new byte[NetworkHeader.SIZE];
                    msg.get(hdrBytes);

                    ByteBuffer hdrBuff = ByteBuffer.wrap(hdrBytes);
                    NetworkHeader nh = new NetworkHeader(hdrBuff);

                    // Snag the payload - if any...
                    ByteBuffer payload = null;
                    if(msg.remaining() > 0) {
                        payload = msg.slice();
                    }

                    wsc.incrementReceived();

                    // Let everybody know about it...
                    m_Listeners.onMessage(wsc, nh, hdrBuff, payload);


                } else {
                    android.util.Log.w(TAG, "Received message shorter than the header! Dropping it...");
                }
            }
            else {
                android.util.Log.e(TAG, "Received message from unknown connection!!!");
            }
        }
    }

    @Override
    public void onError(WebSocket conn, Exception ex) {
        android.util.Log.i(TAG, "onError()");

        // Just log for now
        if ( ex != null ) {
            android.util.Log.e(TAG, ex.toString());
        }
    }

    @Override
    public void onStart() {
        android.util.Log.i(TAG, "onStart()");
        // Nothing to do
    }
}