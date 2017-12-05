package msgtools.milesengineering.androidserver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;

import msgtools.milesengineering.msgserver.MsgServerService;

/**
 * Simple utility class - designed to parse and invoke methods on
 * the MainActivity.  It acts as a sort of proxy data model for the list
 */
class AppBroadcastReceiver extends BroadcastReceiver {
    private static final String TAG = AppBroadcastReceiver.class.getSimpleName();
    private AppExpandableListAdapter m_ListAdapter;

    /**
     * Ctor
     * @param activity the main activity we're working with
     * @param adapter the list adapter managed by the app
     */
    public AppBroadcastReceiver(MainActivity activity, AppExpandableListAdapter adapter) {
        super();
        m_ListAdapter = adapter;

        // Register to receive intents from the MsgServer for UI updates...
        // Add new intents here...
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(MsgServerService.INTENT_SEND_SERVERS);
        intentFilter.addAction(MsgServerService.INTENT_SEND_CONNECTIONS);
        intentFilter.addAction(MsgServerService.INTENT_SEND_NEW_CONNECTION);
        intentFilter.addAction(MsgServerService.INTENT_SEND_CLOSED_CONNECTION);
        activity.registerReceiver(this, intentFilter);
    }

    /**
     * This is where we process Broadcast events from the MsgServerService.  Don't forget to
     * register for new intents in the constructor if you add more...
     *
     * @param context the working app context
     * @param intent the intent to process
     */
    @Override
    public void onReceive(final Context context, final Intent intent) {
        android.util.Log.i(TAG, "AppBroadcastReceiver::onReceive(...)");
        if (intent.getAction().equals(MsgServerService.INTENT_SEND_SERVERS))
            handleServersIntent(intent);
        else if (intent.getAction().equals(MsgServerService.INTENT_SEND_CONNECTIONS)) {
            handleConnectionsIntent(intent);
        }
        else if (intent.getAction().equals(MsgServerService.INTENT_SEND_NEW_CONNECTION)) {
            handleNewConnectionIntent(intent);
        }
        else if (intent.getAction().equals(MsgServerService.INTENT_SEND_CLOSED_CONNECTION)) {
            handleClosedConnectionIntent(intent);
        }
    }

    /**
     * Process an updated server list from the server...
     * @param intent the intent to handle...
     */
    private void handleServersIntent(Intent intent) {
        android.util.Log.i(TAG, "handleServersIntent");
        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        m_ListAdapter.setServers(json);
    }

    /**
     * Process the full connections list.  Usually in response to a request for all connections.
     * @param intent Intent with the list of connections
     */
    private void handleConnectionsIntent(Intent intent) {
        android.util.Log.i(TAG, "handleConnectionsIntent");
        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        m_ListAdapter.setConnections(json);
    }

    private void handleNewConnectionIntent(Intent intent) {
        android.util.Log.i(TAG, "handleNewConnectionIntent");

        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        m_ListAdapter.addNewConnection(json);
    }

    private void handleClosedConnectionIntent(Intent intent) {
        android.util.Log.i(TAG, "handleClosedConnectionIntent");

        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        m_ListAdapter.removeClosedConnection(json);
    }
}
