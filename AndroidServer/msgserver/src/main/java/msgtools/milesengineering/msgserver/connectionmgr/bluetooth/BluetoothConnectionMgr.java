package msgtools.milesengineering.msgserver.connectionmgr.bluetooth;

import java.io.IOException;

import msgtools.milesengineering.msgserver.connectionmgr.BaseConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgr;
import msgtools.milesengineering.msgserver.connectionmgr.IConnectionMgrListener;

/**
 * This is a Bluetooth SPP oriented connection manager.  It does not handle pairing, or discovery.
 * It only looks for new connections and tries to establish an SPP profile for data exchange.
 */

public class BluetoothConnectionMgr extends BaseConnectionMgr implements IConnectionMgr {
    private static final String TAG = BluetoothConnectionMgr.class.getSimpleName();

    public BluetoothConnectionMgr(IConnectionMgrListener listener) {
        super(listener);
    }

    //
    // Base Connection Mgr methods...
    @Override
    protected void setup() throws IOException {

    }

    @Override
    protected void execute() throws IOException {
        try {
            Thread.sleep(1000); // Temporary until we fill this in
        } catch (InterruptedException e) {

        }e.printStackTrace();
    }

    @Override
    protected void cleanup() {

    }
}
