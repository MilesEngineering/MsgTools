package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.nio.ByteBuffer;
import java.util.UUID;

import headers.BluetoothHeader;
import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.ConnectionListenerHelper;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;

/**
 * Thread for managing Bluetooth SPP connections
 */
class BluetoothConnectionThread extends Thread implements IConnection {
    private final static String TAG = BluetoothConnectionThread.class.getSimpleName();

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private WeakReference<ConnectionListenerHelper> m_Listeners;
    private BluetoothDevice m_Device;
    private BluetoothSocket m_Socket;
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

            // Connect to the remote device.  This will block until connection, or about
            // 12 seconds elapse.
            m_Socket.connect();

            m_Connected = true;

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
            Thread.sleep(15000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        requestHalt();

        // Notify everyone we have a new message
//        ConnectionListenerHelper listeners = m_Listeners.get();
//        if ( listeners != null )
//            listeners.onNewConnection(this);
    }

    private void cleanup() {
        android.util.Log.d(TAG, "cleanup()");

        // Close the socket, and send out a closure event if we connected
        try {
            if (m_Socket != null) {
                m_Socket.close();
            }
        } catch (IOException e) {
            android.util.Log.w(TAG, e.getMessage());
            e.printStackTrace();
        } finally {
            if (m_Connected == true ) {
                m_Connected = false;

                // Notify everyone we've closed
                ConnectionListenerHelper listeners = m_Listeners.get();
                if (listeners != null)
                    listeners.onClosedConnection(this);
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

        // TODO: Add code to translate to a BluetoothHeader and send

        return false;
    }

    @Override
    public String getDescription() {
        android.util.Log.d(TAG, "getDescription()");

        return String.format("%s <%s>", m_Device.getName(), m_Device.getAddress());
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
        requestHalt();
    }
}
