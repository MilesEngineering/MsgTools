package msgtools.milesengineering.msgserver.connectionmgr;

import java.nio.ByteBuffer;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;

import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.MessageLogger;

/**
 * This thread manages a queue of messages, dispatching them to various clients
 * and logs.  This is done to avoid blocking sending threads with multiple registered
 * receivers and logging.  We found that Bluetooth is fairly sensitive to receive delays
 * and back pressure on the incoming buffers.
 */

public class MessageRouterThread extends Thread implements IConnectionMgrListener {
    private final static String TAG = MessageRouterThread.class.getSimpleName();
    private boolean m_HaltRequested;

    private ConcurrentHashMap<IConnection,IConnection> m_Connections =
            new ConcurrentHashMap<IConnection,IConnection>();
    private LinkedBlockingQueue<Message> m_BlockingQueue = new LinkedBlockingQueue<Message>();

    private class Message {
        public IConnectionMgr mgr;
        public IConnection src;
        public NetworkHeader hdr;
        public ByteBuffer hdrBuf;
        public ByteBuffer pldBuf;
    }

    public MessageRouterThread( MessageLogger logger ) {
        android.util.Log.d(TAG, "ctor");

    }

    /**
     * Request that the router thread stops - you can join this class if you want to wait for it
     */
    public void requestHalt() {
        m_HaltRequested = true;
    }

    @Override
    public void run() {

    }

    @Override
    public void onNewConnection(IConnectionMgr mgr, IConnection newConnection) {

    }

    @Override
    public void onClosedConnection(IConnectionMgr mgr, IConnection closedConnection) {

    }

    @Override
    public void onMessage(IConnectionMgr mgr, IConnection srcConnection, NetworkHeader networkHeader, ByteBuffer header, ByteBuffer payload) {

    }
}
