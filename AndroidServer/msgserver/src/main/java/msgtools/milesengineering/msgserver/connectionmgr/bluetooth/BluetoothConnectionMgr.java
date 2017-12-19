package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
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

public class BluetoothConnectionMgr extends BaseConnectionMgr implements IConnectionMgr,
        IConnectionMgrListener {
    private static final String TAG = BluetoothConnectionMgr.class.getSimpleName();
    private static final String SERVER_NAME = "AndroidServer";

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private String m_Description = "Uninitialized";
    private BluetoothAdapter m_BluetoothAdapter;
    private BluetoothServerSocket m_ServerSocket;

    private WeakReference<Context> m_HostContext;

    private long m_StartupTime = new Date().getTime(); // To keep time within 32 bits we'll send a delta from server start

    public BluetoothConnectionMgr(IConnectionMgrListener listener, Context hostContext) {
        super(listener);

        // Add ourself as a listener as well so we can keep tabs on our own device list
        addListener(this);

        // Init a broadcast receiver that will invoke APIs on this class to get stuff
        // done in response to Bluetooth events...
        new BluetoothBroadcastReceiver(hostContext, this);

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
            m_Description = String.format("%s <%s>", m_BluetoothAdapter.getName(),
                    m_BluetoothAdapter.getAddress() );
            try {
                // SPP_UUID is the app's UUID string and also a well known SPP value
                m_ServerSocket = m_BluetoothAdapter.listenUsingRfcommWithServiceRecord(SERVER_NAME, SPP_UUID);
            } catch (IOException e) {
                m_Description = e.getMessage();
            }
        }
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
                        getListeners(), m_StartupTime);
                connection.start();
            }
        }
    }

    @Override
    protected void execute() throws IOException {
        try {
            Thread.sleep(1000); // Temporary until we fill this in
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void cleanup() {
        android.util.Log.i(TAG, "cleanup()");
    }

    //
    // Connection manager listener interface
    //
    @Override
    public void onNewConnection(IConnectionMgr mgr, IConnection newConnection) {
        // If our thread connected then add the new connection to the base class tracking
        // so it's automatically cleaned up when the connection manager is halted.
        if (newConnection instanceof BluetoothConnectionThread)
            addConnection(newConnection);
    }

    @Override
    public void onClosedConnection(IConnectionMgr mgr, IConnection closedConnection) {
        // If our thread disconnected then remove the connection from the base class tracking
        if (closedConnection instanceof BluetoothConnectionThread)
            removeConnection(closedConnection);
    }

    @Override
    public void onMessage(IConnectionMgr mgr, IConnection srcConnection, NetworkHeader networkHeader, ByteBuffer header, ByteBuffer payload) {
        // Do nothing
    }
}
