package msgtools.milesengineering.msgserver;

import android.app.Service;
import android.content.ComponentName;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Handler;
import android.os.IBinder;
import android.os.Message;
import android.os.Messenger;
import android.widget.Toast;

/**
 * The main MsgServerService class.  This sets up a service thread, manages incoming messages
 * for API requests, and broadcasts intents to interested clients for new and dropped connections.
 */
public class MsgServerService extends Service {
    private static final String TAG = MsgServerService.class.getSimpleName();

    public  static final String INTENT_ACTION = "msgtools.milesengineering.msgserver.MsgServerServiceAction";

    private Messenger m_MsgHandler;

    /**
     * Private utility class that processes Messages from bound clients
     */
    private class MsgServerAPIHandler extends Handler {
        @Override
        public void handleMessage(Message msg) {
            switch(msg.what) {
                default:
                    android.util.Log.w(TAG, "Unknown message type received by MsgServer.");
                    super.handleMessage(msg);
            }
        }
    }

    public MsgServerService() {
        super();
    }

    @Override
    public void onCreate() {
        android.util.Log.i(TAG, "onCreate()");
        Toast.makeText(this, "MsgServer Service Starting...", Toast.LENGTH_SHORT).show();

        m_MsgHandler = new Messenger(new MsgServerAPIHandler());

        // TODO: Spin up our message handling thread and ConnectionManagers
    }

    @Override
    public void onDestroy() {
        android.util.Log.i(TAG, "onDestroy()");
        Toast.makeText(this, "MsgServer Service Being Destroyed...", Toast.LENGTH_SHORT).show();

        // TODO: Stop our message handling loop and close all connections etc.
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        android.util.Log.i(TAG, "onStartCommand(...)");

        if (flags == START_FLAG_REDELIVERY) {
            return START_NOT_STICKY;
        }

        // MODEBUG: Send a broadcast event to test App receipt
        Intent sendIntent = new Intent();
        sendIntent.setAction(MsgServerService.INTENT_ACTION);
        sendIntent.putExtra(Intent.EXTRA_TEXT, "TEST SERVER");

        sendBroadcast(sendIntent);

        return START_STICKY;
    }

    //
    // Service binding stuff...
    //
    @Override
    public IBinder onBind(Intent intent) {
        android.util.Log.i(TAG, "onBind(...)");
        return m_MsgHandler.getBinder();
    }

    @Override
    public void onRebind(Intent intent) {
        android.util.Log.i(TAG, "onRebind(...)");
        // TODO: reset any state based on binding
    }

    @Override
    public boolean onUnbind(Intent intent) {
        android.util.Log.i(TAG, "onUnbind(...)");
        return super.onUnbind(intent);
    }

}
