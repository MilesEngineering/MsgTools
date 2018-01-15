package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

import java.lang.ref.WeakReference;

/**
 * Broadcast Receiver for Bluetooth events.  This class basically converts the received
 * intents into API call on the BluetoothConnectionMgr.
 */

class BluetoothBroadcastReceiver extends BroadcastReceiver {
    private WeakReference<BluetoothConnectionMgr> m_ConnectionMgr;

    public BluetoothBroadcastReceiver(Context context, BluetoothConnectionMgr connectionMgr) {
        m_ConnectionMgr = new WeakReference<BluetoothConnectionMgr>(connectionMgr);

        IntentFilter filter = new IntentFilter();

        // TOOD: Register for all intents of interest here...

        context.registerReceiver(this, filter);
    }

    public void unregister(Context context) {
        context.unregisterReceiver(this);
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        // TODO: Handle all intents of interest here...
    }
}
