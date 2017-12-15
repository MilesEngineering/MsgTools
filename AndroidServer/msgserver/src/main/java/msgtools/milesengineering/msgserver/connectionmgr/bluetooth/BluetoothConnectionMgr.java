package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import java.io.IOException;
import java.lang.ref.WeakReference;
import java.util.Set;
import java.util.UUID;

import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;

/**
 * This is a Bluetooth SPP oriented connection manager.  It does not handle pairing, or discovery.
 * It only looks for new connections and tries to establish an SPP profile for data exchange.
 */

public class BluetoothConnectionMgr extends BaseConnectionMgr implements IConnectionMgr {
    private static final String TAG = BluetoothConnectionMgr.class.getSimpleName();
    private static final String SERVER_NAME = "AndroidServer";

    // Setup a constant with the well known SPP UUID
    private static final UUID SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");

    private String m_Description = "Uninitialized";
    private BluetoothAdapter m_BluetoothAdapter;
    private BluetoothServerSocket m_ServerSocket;

    private WeakReference<Context> m_HostContext;

    public BluetoothConnectionMgr(IConnectionMgrListener listener, Context hostContext) {
        super(listener);

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
            m_HostContext = new WeakReference<Context>(hostContext);

            try {
                // SPP_UUID is the app's UUID string and also a well known SPP value
                m_ServerSocket = m_BluetoothAdapter.listenUsingRfcommWithServiceRecord(SERVER_NAME, SPP_UUID);
            } catch (IOException e) {
                m_Description = e.getMessage();
            }
        }

        // MODEBUG: Get and print the list of devices and try to connect to everything...
        Set<BluetoothDevice> devs = m_BluetoothAdapter.getBondedDevices();
        for( BluetoothDevice dev : devs ) {
            BluetoothConnectionThread connection = new BluetoothConnectionThread(dev,
                    getListeners());
            connection.start();
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


        // MODEBUG
        // Handy page - file:///Users/mosminer/Library/Android/sdk/docs/guide/topics/connectivity/bluetooth.html#QueryingPairedDevices

        // Once we have confirmed BT is available get a list of bonded devices
        // and look for the one that is connected.
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
}
