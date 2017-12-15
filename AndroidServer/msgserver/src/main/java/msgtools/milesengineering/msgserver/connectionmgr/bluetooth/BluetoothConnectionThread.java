package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.WeakReference;
import java.nio.ByteBuffer;
import java.util.UUID;

import headers.BluetoothHeader;
import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.ConnectionListenerHelper;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;

/**
 * Thread for managing Bluetooth SPP connections. This class is threadsafe, but due to the
 * IO stream blocking is difficult to make threadsafe in a simple way.  We can't
 * block callers to sendMessage and other functions while waiting for data to show up.
 *
 * Keep this in mind when making modifications.
 */

// TODO: This class needs to be threadsafe...
class BluetoothConnectionThread extends Thread implements IConnection {
    private final static String TAG = BluetoothConnectionThread.class.getSimpleName();
    private final Object m_SocketLock = new Object();   // Lock for socket management
    private final Object m_OutputLock = new Object();   // Lock for socket management

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private static final int INITIAL_READBUF_SIZE = BluetoothHeader.SIZE;   // Always guarantee we can read a header

    private WeakReference<ConnectionListenerHelper> m_Listeners;
    private BluetoothDevice m_Device;
    private BluetoothSocket m_Socket;

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

    private BluetoothHeader m_BluetoothHeader;
    private ByteBuffer m_Payload;

    public BluetoothConnectionThread(BluetoothDevice device, ConnectionListenerHelper listeners) {
        android.util.Log.d(TAG, "BluetoothConnectionThread(...)");
        m_Device = device;
        m_Listeners = new WeakReference<ConnectionListenerHelper>(listeners);
    }

    /**
     * Stop processing this connection and close it.  Same as close.
     */
    public void requestHalt() {
        android.util.Log.d(TAG, "requestHalt()");
        m_HaltRequested = true;
    }


    @Override
    public void run() {
        android.util.Log.d(TAG, "run()");

        setup();

        while( m_HaltRequested == false )
            execute();

        cleanup();
    }

    private void setup() {
        android.util.Log.d(TAG, "setup()");

        try {
            // Initialize an SPP socket
            m_Socket = m_Device.createRfcommSocketToServiceRecord(SPP_UUID);

            synchronized (m_SocketLock) {
                // Connect to the remote device.  This will block until connection, or about
                // 12 seconds elapse.
                m_Socket.connect();

                // Setup our IO...
                m_Input = m_Socket.getInputStream();

                synchronized (m_OutputLock) {
                    m_Output = m_Socket.getOutputStream();
                }
                m_ReadBuffer = new byte[INITIAL_READBUF_SIZE];

                m_Connected = true;
            }

            // Notify everyone we've connected
            ConnectionListenerHelper listeners = m_Listeners.get();
            if ( listeners != null )
                listeners.onNewConnection(this);

        } catch (IOException ioe) {
            android.util.Log.d(TAG, ioe.getMessage());
            android.util.Log.i(TAG, "BluetoothSocket unable to connect!");
            requestHalt();
        }


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
                NetworkHeader nh = getNetworkHeader(new BluetoothHeader(m_HeaderBuf));

                // Notify everyone we have a new message
                ConnectionListenerHelper listeners = m_Listeners.get();
                if ( listeners != null )
                    listeners.onMessage(this, nh, nh.GetBuffer(), m_PayloadBuf);

                // Reset for the next message - you might be tempted to optimize and
                // set the position on the header buf to 0.  DON'T!  You have no
                // idea how the buffer is being used once we broadcast it to the listeners
                // and we don't want to overwrite data somebody else may be using.
                m_HeaderBuf = null;
                m_PayloadBuf = null;
            }
        } catch (IOException ioe) {
            android.util.Log.i(TAG, "BT socket disconnected.  Cleaning up.");
            ioe.printStackTrace();
            requestHalt();
        }
    }

    private void cleanup() {
        android.util.Log.d(TAG, "cleanup()");

        // Close the socket, and send out a closure event if we connected
        synchronized(m_SocketLock) {
            try {
                if (m_Socket != null)
                    m_Socket.close();
            } catch (IOException e) {
                android.util.Log.i(TAG, e.getMessage());
                e.printStackTrace();
            } finally {
                if (m_Connected == true) {
                    m_Connected = false;

                    // Notify everyone we've closed
                    ConnectionListenerHelper listeners = m_Listeners.get();
                    if (listeners != null)
                        listeners.onClosedConnection(this);
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
        android.util.Log.d(TAG, "sendMessage(...)");
        boolean retVal = false;
        synchronized (m_OutputLock) {
            if (m_Connected == true) {
                // Convert to a BluetoothHeader
                BluetoothHeader bth = getBluetoothHeader(networkHeader);
                
                // Some implementations aren't happy if you send the header and payload in two
                // writes.  Concatenate the hdr and payload into a single array so we can write
                // it in one go.  This is definitely inefficient.
                ByteBuffer hdr = bth.GetBuffer();
                ByteBuffer sendBuf = ByteBuffer.allocate( hdr.capacity() + payloadBuff.capacity() );
                hdr.position(0);
                sendBuf.put(hdr);
                payloadBuff.position(0);
                sendBuf.put(payloadBuff);

                try {
                    if (m_Output != null) {
                        // Write out data.
                        m_Output.write(sendBuf.array());

                        retVal = true;
                        m_MessagesSent++;
                    }
                } catch (IOException e) {
                    android.util.Log.i(TAG, "Error writing message to BT socket.  Socket assumed closed...");
                    e.printStackTrace();
                    requestHalt();
                }
            }
        }
        return retVal;
    }

    @Override
    public String getDescription() {
        android.util.Log.d(TAG, "getDescription()");

        String retVal = "Uninitialized";
        if (m_Device != null)
            retVal = String.format("%s <%s>", m_Device.getName(), m_Device.getAddress());

        return retVal;
    }

    @Override
    public String getProtocol() {
        android.util.Log.d(TAG, "getProtocol()");

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
        if ( m_Connected == true ) {
            synchronized (m_SocketLock) {
                try {
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

    private NetworkHeader getNetworkHeader(BluetoothHeader bluetoothHeader) {
        NetworkHeader retVal = new NetworkHeader();
        retVal.SetMessageID(bluetoothHeader.GetMessageID());
        retVal.SetDataLength(bluetoothHeader.GetDataLength());

        // TODO: Use reflection to copy all like named fields

        return retVal;
    }

    private BluetoothHeader getBluetoothHeader(NetworkHeader networkHeader) {
        BluetoothHeader retVal = new BluetoothHeader();
        retVal.SetMessageID(networkHeader.GetMessageID());
        retVal.SetDataLength(networkHeader.GetDataLength());

        // TODO: Use reflection to copy all like named fields

        return retVal;
    }

}
