package msgtools.milesengineering.msgserver.connectionmgr.websocket;

import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;

import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;

/**
 * ConnectionMgr implementation for handling Websocket connections. We're basically
 * wrapping the org.java-websocket package into a standard interface for our service.
 */
public class WebsocketConnectionMgr extends WebSocketServer implements IConnectionMgr {
    private static final String TAG = WebsocketConnectionMgr.class.getSimpleName();

    /**
     * Private implementation of our underlying websocket connection.
     */
    private class WebsocketConnection implements IConnection {

        //
        // IConnection methods
        //
        @Override
        public boolean sendMessage(long msgId, ByteBuffer payloadBuff) {
            return false;
        }

        @Override
        public int getMessagesSent() {
            return 0;
        }

        @Override
        public int getMessagesReceived() {
            return 0;
        }

        @Override
        public void close() throws IOException {

        }

        public WebsocketConnection(WebSocket ws) {

        }
    }

    //
    // IConnectionMgr Methods
    //
    @Override
    public void addListener(IConnectionMgrListener listener) {

    }

    @Override
    public boolean removeListener(IConnectionMgrListener listener) {
        return false;
    }

    @Override
    public void requestHalt() {

    }

    @Override
    public boolean haltPending() {
        return false;
    }

    //
    // WebSocketServerMethods
    //
    @Override
    public void onOpen(WebSocket conn, ClientHandshake handshake) {

    }

    @Override
    public void onClose(WebSocket conn, int code, String reason, boolean remote) {

    }

    @Override
    public void onMessage(WebSocket conn, String message) {

    }

    @Override
    public void onError(WebSocket conn, Exception ex) {

    }

    @Override
    public void onStart() {

    }

    //
    // Supporting Methods
    //
    public WebsocketConnectionMgr(InetSocketAddress addr ) {
        super(addr);
        android.util.Log.i(TAG, "WebsocketConnectionMgr(...)");
    }
}
