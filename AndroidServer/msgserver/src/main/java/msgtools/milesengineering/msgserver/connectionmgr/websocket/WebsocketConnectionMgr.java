package msgtools.milesengineering.msgserver.connectionmgr.websocket;

import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.DefaultSSLWebSocketServerFactory;
import org.java_websocket.server.WebSocketServer;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.ref.WeakReference;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.security.KeyManagementException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.UnrecoverableKeyException;
import java.security.cert.CertificateException;
import java.util.Hashtable;

import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;

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
    private static final String CERTIFICATE_FILENAME = "/sdcard/MessageServer/androidserver.p12";
    private static final String PASSWORD_FILENAME = "/sdcard/MessageServer/password.txt";
    private final Object m_Lock = new Object();

    private Hashtable<WebSocket, WebsocketConnection> m_Connections =
            new Hashtable<WebSocket, WebsocketConnection>();
    private ConnectionListenerHelper m_Listeners;
    private boolean m_HaltPending;
    private InetSocketAddress m_SocketAddress;
    private boolean m_SecureSockets = false;

    public WebsocketConnectionMgr(InetSocketAddress addr, IConnectionMgrListener listener ) {
        super(addr);
        android.util.Log.i(TAG, "WebsocketConnectionMgr(...)");

        // Enable SSL with a self signed cert
        try {

            FileInputStream keyfile = new FileInputStream(CERTIFICATE_FILENAME);
            String passStr = new BufferedReader(new InputStreamReader(new FileInputStream(PASSWORD_FILENAME))).readLine();
            char[] password = passStr.toCharArray();

            // Load a keystore - we're assuming a cert and private key are present and the
            // store is in PKCS12 format
            KeyStore keyStore = KeyStore.getInstance("PKCS12");
            keyStore.load(keyfile, password);

            // Initialize a key manager from the KeyStore
            String defaultAlg = KeyManagerFactory.getDefaultAlgorithm();
            KeyManagerFactory kmf = KeyManagerFactory.getInstance(defaultAlg);
            kmf.init(keyStore, password);

            // Initialize a TrustManager from the keystore
            defaultAlg = TrustManagerFactory.getDefaultAlgorithm();
            TrustManagerFactory tmf = TrustManagerFactory.getInstance(defaultAlg);
            tmf.init(keyStore);

            // Setup our SSL context
            SSLContext sslContext = SSLContext.getInstance("TLS");
            sslContext.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);
            setWebSocketFactory(new DefaultSSLWebSocketServerFactory(sslContext));
            m_SecureSockets = true;

        } catch (KeyManagementException e) {
            android.util.Log.w(TAG, "Unable to setup TLS Key Management");
            android.util.Log.w(TAG, e.getMessage());
        } catch (NoSuchAlgorithmException e) {
            android.util.Log.w(TAG, "Unable to find TLS Algorithm");
            android.util.Log.w(TAG, e.getMessage());
        } catch (CertificateException e) {
            android.util.Log.w(TAG, "Invalid certificate");
            android.util.Log.w(TAG, e.getMessage());
        } catch (KeyStoreException e) {
            android.util.Log.w(TAG, "Exception initializing key store - bad password?");
            android.util.Log.w(TAG, e.getMessage());
        } catch (IOException e) {
            android.util.Log.w(TAG, "Didn't find a certificate file - setting up for non-SSL sockets");
            android.util.Log.w(TAG, e.getMessage());
        } catch (UnrecoverableKeyException e) {
            android.util.Log.w(TAG, "Key lost");
            android.util.Log.w(TAG, e.getMessage());
        }

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
        public String getProtocol() { return m_SecureSockets ? "WSS":"WS"; }

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
    } // End of WebsocketConnection helper class

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
    public String getProtocol() { return m_SecureSockets ? "WSS":"WS"; }

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