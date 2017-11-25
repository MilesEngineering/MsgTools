package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.content.Context;
import android.content.Intent;
import android.widget.Toast;

import java.io.IOException;
import java.lang.ref.WeakReference;

import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;

/**
 * This is a Bluetooth SPP oriented connection manager.  It does not handle pairing, or discovery.
 * It only looks for new connections and tries to establish an SPP profile for data exchange.
 */

public class BluetoothConnectionMgr extends BaseConnectionMgr implements IConnectionMgr {
    private static final String TAG = BluetoothConnectionMgr.class.getSimpleName();
    private BluetoothAdapter m_BluetoothAdapter;

    private WeakReference<Context> m_HostContext;

    public BluetoothConnectionMgr(IConnectionMgrListener listener, Context hostContext) {
        super(listener);
        m_HostContext = new WeakReference<Context>(hostContext);
    }

    //
    // Base Connection Mgr methods...
    @Override
    protected void setup() throws IOException {
        android.util.Log.i(TAG, "setup()");

        // We require Bluetooth so make sure it's supported and enabled.
        // If it's disabled then enable it anyway.
        Context context = m_HostContext.get();

        m_BluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (m_BluetoothAdapter == null) {
            // Device does not support Bluetooth
            android.util.Log.e(TAG, "Bluetooth not supported!");
            if(context != null) {
                Toast.makeText(context, "Bluetooth is not supported on this device",
                        Toast.LENGTH_LONG).show();
            }
            requestHalt();
        } else if (m_BluetoothAdapter.isEnabled()) {
            // Device does not support Bluetooth
            android.util.Log.e(TAG, "Bluetooth not enabled!");
            if(context != null) {
                Toast.makeText(context, "Bluetooth is not enabled",
                        Toast.LENGTH_LONG).show();
            }
            requestHalt();
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
}
