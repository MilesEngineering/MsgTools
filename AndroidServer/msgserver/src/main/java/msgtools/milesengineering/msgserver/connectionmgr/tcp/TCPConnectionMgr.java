package msgtools.milesengineering.msgserver.connectionmgr.tcp;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketOptions;
import java.net.StandardSocketOptions;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedSelectorException;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.Set;

import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;
import msgtools.milesengineering.msgserver.connectionmgr.utils;

/**
 * This class opens a TCP server socket and listens for incoming
 * connections.
 */
public class TCPConnectionMgr extends BaseConnectionMgr {
    private static final String TAG = TCPConnectionMgr.class.getSimpleName();
    private static final int SELECT_TIMEOUT = 1000; // in ms

    private ServerSocketChannel m_ServerChannel;
    private Selector m_Selector;

    private InetSocketAddress m_SocketAddress;

    /**
     * Private implementation of a IConnection specific to TCP Sockets.
     */
    private class TCPConnection implements IConnection {
        private int m_SentCount = 0;
        private int m_RecvdCount = 0;
        private WeakReference<SocketChannel> m_Channel;

        //
        // Buffers for pulling header and payload bytes.
        // These are used as state variables for reading and
        // parsing messages by the execute method.  Don't muck
        // with then in this class!  Also don't muck with them
        // in any other thread!
        //
        public ByteBuffer m_HeaderBuff;
        public ByteBuffer m_PayloadBuff;

        public TCPConnection(SocketChannel channel, int headerSize) {
            m_Channel = new WeakReference<SocketChannel>(channel);
        }

        @Override
        public boolean sendMessage(NetworkHeader networkHeader, ByteBuffer hdrBuff,
                                   ByteBuffer payloadBuff) {
            boolean retVal = true;

            android.util.Log.d(TAG, "TCPConnection:sendMessage(hdrBuffLen=" + hdrBuff.capacity() +
                    ", payloadBuffLen="+payloadBuff.capacity());

            if ( m_Channel != null ) {
                SocketChannel channel = m_Channel.get();
                if ( channel != null && channel.isConnected() == true ) {
                    try {
                        hdrBuff.position(0);
                        payloadBuff.position(0);

                        // TODO: MessageScope doesn't handle two independent write requests correctly
                        // It treats them as two messages.  GitHub issue #18.
                        // Stacking the two buffers into one to get around this.  We'll want to remove this
                        // later as it's just wasting CPU and thrashing memory.
                        ByteBuffer sendBuf = ByteBuffer.allocate(hdrBuff.capacity()+payloadBuff.capacity());
                        sendBuf.put(hdrBuff);
                        sendBuf.put(payloadBuff);

                        sendBuf.position(0);
                        while (sendBuf.remaining() > 0)
                            channel.write(sendBuf);

// TODO: Put this back in when Issue #18 is fixed - per above
//                        while(hdrBuff.remaining() > 0)
//                            channel.write(hdrBuff);
//
//                        while( payloadBuff.remaining() > 0)
//                            channel.write(payloadBuff);

                        m_SentCount++;
                    } catch (IOException ioe) {
                        retVal = false;
                    }
                }
            }

            return retVal;
        }

        @Override
        public String getDescription() {
            String retVal = "Unknown client";
            SocketChannel chan = m_Channel.get();
            if ( chan != null ) {
                try {
                    retVal = chan.getRemoteAddress().toString();
                    retVal = retVal.substring(1);
                } catch( IOException ioe ) {
                    retVal = ioe.getMessage();
                }
            }
            return retVal;
        }

        @Override
        public String getProtocol() { return "TCP"; }

        @Override
        public int getMessagesSent() {
            return m_SentCount;
        }

        @Override
        public int getMessagesReceived() {
            return m_RecvdCount;
        }

        @Override
        public void close() throws IOException {
            if (m_Channel != null) {
                m_Channel.get().close();
                m_Channel = null;
            }
        }

        /**
         * Increment the number of messages received by one
         */
        public void addMessageReceived() {
            // Increment msg received count by one
            m_RecvdCount++;
        }
    }

    /**
     * Instantiate a new instance bound to the indicated SocketAddress
     * @see ServerSocketChannel bind() for more details
     * @param addr Address to bind to
     */
    public TCPConnectionMgr(InetSocketAddress addr, IConnectionMgrListener listener) {
        super(listener);
        android.util.Log.i(TAG, "TCPConnectionMgr ctor");

        // Don't start anything up until start is called...
        m_SocketAddress = addr;
    }

    @Override
    public String getProtocol() { return "TCP"; }

    @Override
    public String getDescription() {
        InetAddress ia = utils.getHostAddress();
        String retVal = ia.toString() + ":" + m_SocketAddress.getPort();
        return retVal.substring(1);
    }

    @Override
    protected void setup() throws IOException {
        // Fire up a server channel.
        android.util.Log.i(TAG, "setup()");
        m_ServerChannel = ServerSocketChannel.open();
        m_ServerChannel.setOption(StandardSocketOptions.SO_REUSEADDR, true);
        m_ServerChannel.bind(m_SocketAddress);

        // We want to periodically return so the base class can test for a halt
        // request. Make this non-blocking.  We will throttle back on the select handling
        // with a timeout to avoid running open loop and wasting CPU.
        m_ServerChannel.configureBlocking(false);

        m_Selector = Selector.open();

        m_ServerChannel.register( m_Selector, m_ServerChannel.validOps() );

    }

    @Override
    protected void execute() throws IOException  {
        // android.util.Log.d(TAG, "execute()");
        try {
            // Now check for data...
            if (m_Selector.select(SELECT_TIMEOUT) > 0) {

                Set<SelectionKey> keys = m_Selector.selectedKeys();
                synchronized(keys) {
                    for (SelectionKey key : keys) {
                        if (key.isValid() == false) {
                            TCPConnection connection = (TCPConnection)key.attachment();
                            key.attach(null);   // Help out the garbage collector

                            // Notify all listeners we're closing this connection
                            // and clean it up...
                            onClosedConnection(connection);
                            key.cancel();

                            continue;
                        }

                        if (key.isAcceptable() == true) {
                            acceptNewConnection();

                        } else if (key.isReadable() == true) {
                            readMessageData(key);
                        }

                    }

                    keys.clear();
                }
            }
        }
        catch(ClosedSelectorException cse) {
            android.util.Log.e(TAG, cse.toString());
            requestHalt();
        }
    }

    private void acceptNewConnection() throws IOException {
        // Accept new connections - keep in mind we're non-blocking here
        SocketChannel newConnection = m_ServerChannel.accept();


        // If we got a new connection set it up for READ selection
        // Also create a new TCPConnection object for our own tracking purposes.
        if (newConnection != null) {
            android.util.Log.d(TAG, "New Connection");
            TCPConnection tcpConn = new TCPConnection(newConnection, NetworkHeader.SIZE);

            // Register with our selector
            newConnection.configureBlocking(false);   // Must be non-blocking
            SelectionKey newKey = newConnection.register(m_Selector, SelectionKey.OP_READ, tcpConn);

            // Enable keep alive to try and kill off zombie connections...
            newConnection.setOption(StandardSocketOptions.SO_KEEPALIVE, new Boolean(true));

            // Notify listeners we have a new connection
            onNewConnection(tcpConn);
        }
    }

    private void readMessageData(SelectionKey key) throws IOException {
        TCPConnection tcpConn = (TCPConnection) key.attachment();
        SocketChannel channel = (SocketChannel) key.channel();

        // TODO: So - problem here - due to the way TCP works (keepalive and all
        // that stuff), if you disconnect the client select starts returning
        // immediately with read status set, but we get 0 bytes.  Which rails
        // the CPU and is really unfriendly.  We could test connection by trying
        // to write, but if the client reconnects short after we lose them
        // you'll botch the data stream and we don't have a good way to resync.
        // We could detect a read of 0 bytes and close the connection but that of
        // isn't very friendly.  Have to ponder some more.

        // No network header?  Then create one...
        if (tcpConn.m_HeaderBuff == null) {
            tcpConn.m_HeaderBuff = ByteBuffer.allocate(NetworkHeader.SIZE);
        }

        // If we have header bytes left to read then read them...
        NetworkHeader hdr = null;
        if (tcpConn.m_HeaderBuff.remaining() > 0) {
            channel.read(tcpConn.m_HeaderBuff);

            // If we have the full header loaded
            if (tcpConn.m_HeaderBuff.remaining() == 0) {
                // Allocate a new NetworkHeader and get the length...
                hdr = new NetworkHeader(tcpConn.m_HeaderBuff);

                // Allocate a buffer for the payload...
                tcpConn.m_PayloadBuff =
                        ByteBuffer.allocate((int) hdr.GetDataLength());
            }
        }

        // If we have the header the read into the payload until we're done
        if (tcpConn.m_HeaderBuff.remaining() == 0) {

            channel.read(tcpConn.m_PayloadBuff);

            if (tcpConn.m_PayloadBuff.remaining() == 0) {
                // Chalk up a new msg received count
                tcpConn.addMessageReceived();

                // If we didn't get the whole payload in one read
                // then the header will be null.  Recreate it.
                if(hdr == null)
                    hdr = new NetworkHeader(tcpConn.m_HeaderBuff);

                // We've got everything we need.  Fire off an onMessage
                // event with the msgId and payload and reset our state
                onMessage(tcpConn, hdr, tcpConn.m_HeaderBuff,
                        tcpConn.m_PayloadBuff);

                // Now reset for the next go
                tcpConn.m_HeaderBuff = null;
                tcpConn.m_PayloadBuff = null;
            }

        }
    }

    @Override
    protected void cleanup() {
        android.util.Log.i(TAG, "cleanup()");

        m_SocketAddress = null;

        try {
            m_Selector.close();
            m_Selector = null;
        }
        catch(Exception e) {
            android.util.Log.w(TAG, e.toString());
        }

        try {
            m_ServerChannel.close();
            m_ServerChannel = null;
        }
        catch(Exception e) {
            android.util.Log.w(TAG, e.toString());
        }
    }
}
