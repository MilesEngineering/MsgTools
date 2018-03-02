package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.Context;
import android.widget.Toast;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.nio.ByteBuffer;
import java.util.Date;
import java.util.Set;
import java.util.UUID;

import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;

/**
 * This is a Bluetooth SPP oriented connection manager.  It does not handle pairing, or discovery.
 * It only looks for bonded connections and tries to establish an SPP connection for data exchange.
 *
 * This class is threaded a bit differently than other connection managers because Bluetooth
 * sockets don't implement a selectable interface.  Therefore each connection is spun up on its
 * own thread, and sends listener events directly for connection etc.
 *
 * The main loop of this class is presently empty.  In the future we can put a retry on bonded devices
 * host a server socket, and other things in the loop.  Meantime it's just snoozing and burning
 * unnecessary CPU. This choice was made to allow us to leverage the BaseConnectionMgr class as
 * it provides more than just a processing thread for us.
 *
 * It's nice to have this class cleanup all the connections it's spawned.  To do that
 * we're making this class a connection event listener itself to maintain an internal
 * list of Bluetooth only connections.  Making this class look a little weird.
 *
 * The other weirdity is we're interested in broadcast Bluetooth intents, which require a top level
 * activity or similar to capture.  Thus we spin up a utility class to receive intents and
 * invoke APIs on this class as a shim.
 */

public class BluetoothConnectionMgr extends BaseConnectionMgr implements IConnectionMgr {
    private static final String TAG = BluetoothConnectionMgr.class.getSimpleName();
    private static final String SERVER_NAME = "AndroidServer";
    private static final int ACCEPT_TIMEOUT = 1000;

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private String m_Description = "Uninitialized";
    private BluetoothAdapter m_BluetoothAdapter;
    private BluetoothServerSocket m_ServerSocket;
    private BluetoothBroadcastReceiver m_BluetoothBroadcastReceiver;

    private WeakReference<Context> m_HostContext;

    public BluetoothConnectionMgr(IConnectionMgrListener listener, Context hostContext) {
        super(listener);

        // Init a broadcast receiver that will invoke APIs on this class to get stuff
        // done in response to Bluetooth events...
        m_BluetoothBroadcastReceiver = new BluetoothBroadcastReceiver(hostContext, this);

        // TODO: Reconsider storing the context - don't think we need to keep it around
        m_HostContext = new WeakReference<Context>(hostContext);

        // We require Bluetooth so make sure it's supported and enabled.
        // If it's disabled then enable it anyway.  We could do all this in the setup
        // method but it's better to fail out now while we're on the main thread.
        m_BluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (m_BluetoothAdapter == null) {
            // Device does not support Bluetooth
            android.util.Log.e(TAG, "Bluetooth not supported!");
            m_Description = "Not Supported";
            if(hostContext != null) {
                Toast.makeText(hostContext, "Bluetooth is not supported on this device",
                        Toast.LENGTH_LONG).show();
            }
            requestHalt();
        } else if (m_BluetoothAdapter.isEnabled() == false) {
            android.util.Log.e(TAG, "Bluetooth not enabled!");
            m_Description = "Not Enabled";
            if(hostContext != null) {
                Toast.makeText(hostContext, "Bluetooth not enabled",
                        Toast.LENGTH_LONG).show();
            }
            requestHalt();
        } else {
            // Note: As of Android 6.0/Marshmallow this will always return an MAC of
            // 02:00:00:00:00:00 for "added security".  A user can still get the MAC in
            // Settings->About->Status.  More details here...
            // https://developer.android.com/about/versions/marshmallow/android-6.0-changes.html#behavior-hardware-id
            m_Description = String.format("%s <%s>", m_BluetoothAdapter.getName(),
                    m_BluetoothAdapter.getAddress() );
        }
    }

    @Override
    public void requestHalt() {
        android.util.Log.i(TAG, "requestHalt()");
        super.requestHalt();

        // Stop receiving BT intents...
        Context context = m_HostContext.get();
        if (context != null)
            m_BluetoothBroadcastReceiver.unregister(context);
    }

    @Override
    public String getProtocol() { return "BT"; }

    @Override
    public String getDescription() { return m_Description; }

    //
    // Base Connection Mgr methods...
    @Override
    protected void setup() throws IOException {
        android.util.Log.i(TAG, "setup()");

        // Get a list of all bonded devices and try to establish an SPP connection
        // We'll probably want something more controlled and elegant in the future
        // but this brute force method will work fine for now.

        // We'll rely on broadcast intents to handle disconnects, new bonded devices,
        // Bluetooth being enabled/disabled, etc...
        if (m_BluetoothAdapter != null) {
            Set<BluetoothDevice> devs = m_BluetoothAdapter.getBondedDevices();
            for (BluetoothDevice dev : devs) {
                BluetoothConnectionThread connection = new BluetoothConnectionThread(dev,
                        this);
                connection.start();
            }

            // Setup an SPP server socket to accept incoming connections.
            try {
                // SPP_UUID is the app's UUID string and also a well known SPP value
                android.util.Log.i(TAG, "Setting up server socket...");
                m_ServerSocket = m_BluetoothAdapter.listenUsingRfcommWithServiceRecord(SERVER_NAME, SPP_UUID);
            } catch (IOException e) {
                m_Description = e.getMessage();
                android.util.Log.e(TAG, e.getMessage());
                android.util.Log.e(TAG, e.getStackTrace().toString());
            }
        }
    }

    @Override
    protected void execute() throws IOException {
        try {
            // All we're going to do here is listen for incoming connections
            // and spawn off receiver conections
            BluetoothSocket newConnection = null;
            android.util.Log.v(TAG, "accept()");
            newConnection = m_ServerSocket.accept( ACCEPT_TIMEOUT );

            android.util.Log.i(TAG, "Accepting connection to " + newConnection.getRemoteDevice().getName());

            BluetoothConnectionThread connection = new BluetoothConnectionThread(newConnection,
                    this);
            connection.start();


        } catch (IOException ioe) {
            // Assuming we just timed out here and this is ok - may need to revisit this if we find
            // other IOException cases are common...
            android.util.Log.v(TAG, "Accept timeout");
        }
    }

    @Override
    protected void cleanup() {
        android.util.Log.i(TAG, "cleanup()");
    }

    //
    // Proxy methods for the BT thread.  This allows us to proxy events into
    // the general manager architecture and leverage our base class code.  Important
    // because there is some plugin logic and other stuff in the base class
    // that we want to retain as common
    //
    void newConnection(IConnection newConnection) {
        // Keep in mind - this is coming in off a Bluetooth Connection Thread
        this.onNewConnection(newConnection);
    }

    void closeConnection(IConnection closedConnection) {
        // Keep in mind - this is coming in off a Bluetooth Connection Thread
        this.onClosedConnection(closedConnection);
    }

    void newMessage(IConnection srcConnection, NetworkHeader networkHeader, ByteBuffer header, ByteBuffer payload) {
        // Keep in mind - this is coming in off a Bluetooth Connection Thread
        this.onMessage(srcConnection, networkHeader, header, payload);
    }
}
