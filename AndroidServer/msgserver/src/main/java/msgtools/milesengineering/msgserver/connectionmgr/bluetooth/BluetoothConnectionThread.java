package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.nio.ByteBuffer;
import java.util.UUID;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import headers.BluetoothHeader;
import headers.NetworkHeader;
import msgplugin.MessageHandler;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;

/**
 * Thread for managing Bluetooth SPP connections. This class is threadsafe, but due to the
 * IO stream blocking is difficult to make threadsafe in a simple way.  We can't
 * block callers to sendMessage and other functions while waiting for data to show up.
 *
 * Keep this in mind when making modifications.
 */

class BluetoothConnectionThread extends Thread implements IConnection {
    private final static String TAG = BluetoothConnectionThread.class.getSimpleName();
    private final Object m_SocketLock = new Object();   // Lock for socket management

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final int INITIAL_READBUF_SIZE = BluetoothHeader.SIZE;   // Always guarantee we can read a header

    private WeakReference<BluetoothConnectionMgr> m_BluetoothConnectionMgr;
    private MessageHandler m_MessageHandler = MessageHandler.getInstance(); // Handler plugin
    private BluetoothDevice m_Device;
    private BluetoothSocket m_Socket;
    private BluetoothSocket m_WrapSocket;

    // Properties used for reading input
    private InputStream m_Input;
    private OutputStream m_Output;
    private byte[] m_ReadBuffer;
    private ByteBuffer m_HeaderBuf;
    private ByteBuffer m_PayloadBuf;

    private boolean m_HaltRequested = false;
    private boolean m_Connected = false;
    private int m_MessagesSent = 0;
    private int m_MessagesReceived = 0;
    private int m_NumConnectionAttempts = 1;
    private int m_ConnectionAttemptsRemaining = 1;

    private BluetoothHeader m_BluetoothHeader;
    private ByteBuffer m_Payload;

    private BTSendThread m_SendThread;

    /**
     * Instantiate a new Bluetooth connection with the given device.  This constructor is a client thread.
     * @param device The device to try and connect to
     * @param bcm The Bluetooth Connection manager we're using
     * @param connectionAttempts How many connection attempts to make.  0 indicates we should only  make one
     * connection attempt and never try to reconnect if we lose connection.  1 or more indicates how many many
     * attempts we'll make before giving up.  If we lose connection we'll try the same number of times to
     * re-establish the connection.  Less than 0 means we should continue to try and connect forever.
     */
    public BluetoothConnectionThread(BluetoothDevice device, BluetoothConnectionMgr bcm, int connectionAttempts) {
        android.util.Log.i(TAG, "BluetoothConnectionThread(device, ...)");
        m_Device = device;
        m_BluetoothConnectionMgr = new WeakReference<BluetoothConnectionMgr>(bcm);

        // Always start with at least 1 connection attempt
        m_ConnectionAttemptsRemaining = connectionAttempts == 0 ? 1 : connectionAttempts;
        m_NumConnectionAttempts = connectionAttempts;
    }

    /**
     * Instantiate a new Bluetooth connection processing thread for the given connection.  This
     * constructor wraps an already connected device.
     * @param connection The connection to wrap
     * @param bcm The Bluetooth Connection manager we're using
     */
    public BluetoothConnectionThread(BluetoothSocket connection, BluetoothConnectionMgr bcm) {
        android.util.Log.i(TAG, "BluetoothConnectionThread(connection, ...)");
        m_Device = connection.getRemoteDevice();
        m_WrapSocket = connection;
        m_BluetoothConnectionMgr = new WeakReference<BluetoothConnectionMgr>(bcm);

        // A server accepted socket should never try to reconnect - we rely on the client
        // to reconnect and BluetoothManager broadcast intents to tell us when we should
        // try to connect to a client device
        m_ConnectionAttemptsRemaining = 0;
        m_NumConnectionAttempts = 0;
    }

    /**
     * Stop processing this connection and close it.  Same as close.
     */
    public void requestHalt() {
        android.util.Log.i(TAG, "requestHalt()");
        m_HaltRequested = true;
    }


    @Override
    public void run() {
        android.util.Log.i(TAG, "run()");

        setup();

        while( m_HaltRequested == false )
            execute();

        cleanup();
    }

    private void setup() {
        android.util.Log.i(TAG, "setup()");

        BluetoothSocket newSocket = m_WrapSocket;

        while (newSocket == null && (m_NumConnectionAttempts < 0 || --m_ConnectionAttemptsRemaining > 0)) {
            try {
                // Initialize an SPP socket - if we were passed a socket to wrap in the ctor
                // then just initialize our IO streams etc.  If not then try to connect to the
                // device we're mapped to...
                newSocket = m_Device.createRfcommSocketToServiceRecord(SPP_UUID);

                // Connect to the remote device.  This will block until connection, for up to about
                // 12 seconds, or until we connect.
                newSocket.connect();

                setSocket(newSocket);

            } catch (IOException ioe) {
                android.util.Log.d(TAG, ioe.getMessage());
                android.util.Log.i(TAG, "BluetoothSocket unable to connect!");
                if ( m_NumConnectionAttempts == 0 || m_ConnectionAttemptsRemaining == 0 ) {
                    requestHalt();
                    android.util.Log.i(TAG, "Connection attempt failed.  Halting.");
                }
                else {
                    android.util.Log.i(TAG, "Attempting to connect");
                    newSocket = null;
                }
            }
        }
    }

    private void setSocket(BluetoothSocket newSocket) throws IOException {
        synchronized (m_SocketLock) {

            // Reset our connection attempts remaining and the socket we're
            // wrapping so we attempt to reconnnect if we lose connection again later
            m_ConnectionAttemptsRemaining = m_NumConnectionAttempts;
            m_WrapSocket = null;

            m_Socket = newSocket;

            // Setup our IO...
            m_Input = m_Socket.getInputStream();
            m_Output = m_Socket.getOutputStream();

            m_ReadBuffer = new byte[INITIAL_READBUF_SIZE];

            m_Connected = true;

            setName(m_Socket.getRemoteDevice().getName());

            // Spin up a send thread
            m_SendThread = new BTSendThread("BT Socket: " + m_Socket.getRemoteDevice().getName());
            m_SendThread.start();
        }

        // Notify everyone we've connected
        BluetoothConnectionMgr bcm = m_BluetoothConnectionMgr.get();
            if ( bcm != null )
                bcm.newConnection(this);
    }

    private void execute() {
        // android.util.Log.d(TAG, "execute()");

        // For now just snooze and bail out...
        try {
            // Three stages here - which we'll implement as a mini inline state machine

            // First, we read enough bytes to create a BluetoothHeader
            // Second, we parse the header to determine payload length and read in the payload
            // Third, we build a Network header from the BT header and fire a new message off

            int bytesRead = 0;

            // Stage 1 - read header
            if ( m_HeaderBuf == null || m_HeaderBuf.remaining() > 0 ) {
                // Allocate a new buffer if we don't have one already...
                m_HeaderBuf = m_HeaderBuf != null ? m_HeaderBuf :
                        ByteBuffer.allocate(BluetoothHeader.SIZE);

                // Read up to capacity bytes 0 this will block until we get data
                // or the socket is closed from under us (which will throw an exception)
                bytesRead = m_Input.read(m_ReadBuffer, 0, m_HeaderBuf.remaining());

                // Stash the bytes into the header buffer
                m_HeaderBuf.put(m_ReadBuffer, 0, bytesRead);
            }

            // Stage 2 - determine payload length.  Assuming HeaderBuf isn't null - which
            // it never should be since we don't reset everyting until we emit a message
            if ( m_HeaderBuf.remaining() == 0 ) {
                // If we haven't allocated a buffer for the payload, then do so now
                if ( m_PayloadBuf == null ) {
                    BluetoothHeader bth = new BluetoothHeader(m_HeaderBuf);
                    m_PayloadBuf = ByteBuffer.allocate(bth.GetDataLength());

                    // Make sure we always have enough room in our read buffer
                    // This will have the effect of automatically determining
                    // the optimal buffer capacity we need for reading.
                    if ( m_PayloadBuf.capacity() > m_ReadBuffer.length )
                        m_ReadBuffer = new byte[m_PayloadBuf.capacity()];
                } else if ( m_PayloadBuf.remaining() > 0 ) {
                    // Now read in payload bytes and save them to our payload
                    bytesRead = m_Input.read(m_ReadBuffer, 0, m_PayloadBuf.remaining());
                    m_PayloadBuf.put(m_ReadBuffer, 0, bytesRead);
                }
            }

            // Stage 3 - if we have full header and payload buffers then we can
            // post process and send out a new message
            if ( m_HeaderBuf.remaining() == 0 && m_PayloadBuf != null && m_PayloadBuf.remaining() == 0 ) {

                m_MessagesReceived++;

                // All messages should be in NetworkHeader format, so do that conversion...
                NetworkHeader nh = m_MessageHandler.getNetworkHeader(new BluetoothHeader(m_HeaderBuf));

                // Notify everyone we have a new message - message Handler has first shot
                BluetoothConnectionMgr bcm = m_BluetoothConnectionMgr.get();
                if (bcm != null)
                    bcm.newMessage(this, nh, nh.GetBuffer(), m_PayloadBuf);

                // Reset for the next message - you might be tempted to optimize and
                // set the position on the header buf to 0.  DON'T!  You have no
                // idea how the buffer is being used once we broadcast it to the listeners
                // and we don't want to overwrite data somebody else may be using.
                m_HeaderBuf = null;
                m_PayloadBuf = null;
            }
        } catch (IOException ioe) {
            android.util.Log.i(TAG, "BT socket disconnected.");
            ioe.printStackTrace();
            setup();
        }
    }

    private void cleanup() {
        android.util.Log.d(TAG, "cleanup()");

        // Shutdown our send thread.  This is done here so all thread ops are on
        // the connection thread - that way don't have to sweat external threadsafety!
        if (m_SendThread != null )
            m_SendThread.requestHalt();


        // Close the socket, and send out a closure event if we connected
        synchronized(m_SocketLock) {
            try {
                if (m_Socket != null && m_Socket.isConnected())
                    m_Socket.close();
            } catch (IOException e) {
                android.util.Log.i(TAG, e.getMessage());
                e.printStackTrace();
            } finally {
                if (m_Connected == true) {
                    m_Connected = false;

                    // Notify everyone we've closed
                    BluetoothConnectionMgr bcm = m_BluetoothConnectionMgr.get();
                    if (bcm != null)
                        bcm.closeConnection(this);
                }
            }
        }
    }

    //
    // IConnection Methods
    //

    @Override
    public boolean sendMessage(NetworkHeader networkHeader, ByteBuffer hdrBuff,
                               ByteBuffer payloadBuff) {
        // android.util.Log.v(TAG, "sendMessage(...)");
        boolean retVal = m_SendThread.sendMessage(networkHeader, payloadBuff);

        if (retVal == false) {
            android.util.Log.e(TAG, "BT Socket send queue full - assuming overload or dead connection. Closing.");
            requestHalt();
        }

        return retVal;
    }

    @Override
    public String getDescription() {
        android.util.Log.v(TAG, "getDescription()");

        String retVal = "Uninitialized";
        if (m_Device != null)
            retVal = String.format("%s <%s>", m_Device.getName(), m_Device.getAddress());

        return retVal;
    }

    @Override
    public String getProtocol() {
        android.util.Log.v(TAG, "getProtocol()");

        return "BT-SPP";
    }

    @Override
    public int getMessagesSent() {
        return m_MessagesSent;
    }

    @Override
    public int getMessagesReceived() {
        return m_MessagesReceived;
    }

    @Override
    public void close() throws IOException {
        android.util.Log.i(TAG, getName() + " close()");
        if ( m_Connected == true ) {
            synchronized (m_SocketLock) {
                try {
                    if (m_Socket.isConnected())
                        m_Socket.close();
                    // Don't set m_Connected to false - we want to
                    // handle that in the cleanup method so we fire off
                    // a connection closed event to all listeners
                }
                catch( Exception e) {
                    e.printStackTrace();
                }
            }
        }

        requestHalt();
    }

    /**
     * Helper class for pumping a queue of messages onto a BT socket on it's own thread
     */
    private class BTSendThread extends Thread {
        private final int MAX_QUEUE_DEPTH = 100;
        private LinkedBlockingQueue<BTSendThread.Message> m_BlockingQueue =
                new LinkedBlockingQueue<BTSendThread.Message>(MAX_QUEUE_DEPTH);
        private boolean m_HaltRequested = false;
        private int m_HighwaterMark = 0;

        public class Message {
            public Message(NetworkHeader header, ByteBuffer payloadBuff) {
                this.networkHeader = header;
                this.payloadBuff = payloadBuff;
            }

            public NetworkHeader networkHeader;
            public ByteBuffer payloadBuff;
        }


        BTSendThread(String name) {
            setName(name);
        }

        public boolean sendMessage(NetworkHeader header, ByteBuffer payloadBuff) {
            BTSendThread.Message msg = new BTSendThread.Message(header, payloadBuff);
            boolean retVal = m_BlockingQueue.offer(msg);

            if ( m_BlockingQueue.size() > m_HighwaterMark ) {
                m_HighwaterMark = m_BlockingQueue.size();
                android.util.Log.i(TAG, String.format("BT: %s - new high water mark = %d", getName(), m_HighwaterMark));
            }

            if ( retVal == false ) {
                android.util.Log.w(TAG, String.format("BT: %s - send queue full - flushing", getName()));
                m_BlockingQueue.clear();
                m_HighwaterMark = 0;

                // try again...
                retVal = m_BlockingQueue.offer(msg);
            }

            return retVal;
        }

        public void requestHalt() { m_HaltRequested = true; }

        @Override
        public void run() {
            android.util.Log.i(TAG, getName() + " running");
            while( m_HaltRequested == false ) {
                // android.util.Log.v(TAG, "sendMessage(...)");

                try {
                    BTSendThread.Message msg = m_BlockingQueue.poll(1, TimeUnit.SECONDS);

                    if (msg != null && m_Connected == true) {

                        // Convert to a BluetoothHeader
                        BluetoothHeader bth = m_MessageHandler.getBluetoothHeader(msg.networkHeader);

                        // No header? Then we can't do a translation so drop the message and move on
                        if (bth != null) {

                            // Some implementations aren't happy if you send the header and payload in two
                            // writes.  Concatenate the hdr and payload into a single array so we can write
                            // it in one go.  This is definitely inefficient.

                            // It's also possible to have a message without a payload so be wary of a null
                            // payload buffer
                            ByteBuffer hdr = bth.GetBuffer();
                            int totalLength = hdr.limit() + (msg.payloadBuff == null ? 0 :
                                    msg.payloadBuff.limit());
                            ByteBuffer sendBuf = ByteBuffer.allocate(totalLength);
                            hdr.position(0);
                            sendBuf.put(hdr);

                            if (msg.payloadBuff != null) {
                                msg.payloadBuff.position(0);
                                sendBuf.put(msg.payloadBuff);
                            }

                            try {
                                if (m_Output != null) {
                                    // Write out data.
                                    byte[] buf = sendBuf.array();
                                    m_Output.write(buf);
                                    m_Output.flush();

                                    m_MessagesSent++;
                                }
                            }
                            catch (IOException e) {
                                android.util.Log.i(TAG, "Error writing message to BT socket.  Socket assumed closed...");
                                e.printStackTrace();
                                requestHalt();
                            }
                            catch (Exception e) {
                                android.util.Log.w(TAG, e.toString());
                            }
                        }
                    }
                }
                catch(InterruptedException ie) {
                    android.util.Log.i(TAG, ie.toString());
                    requestHalt();
                }
            }
            android.util.Log.i(TAG, getName() + " halting");
        }
    }
}
