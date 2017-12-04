package msgtools.milesengineering.androidserver;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.support.annotation.NonNull;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.lang.reflect.Array;
import java.util.Collections;
import java.util.List;

import msgtools.milesengineering.msgserver.MsgServerService;

/**
 * Simple utility class - designed to parse and invoke methods on
 * the MainActivity.  It acts as a sort of proxy data model for the list
 */
class AppBroadcastReceiver extends BroadcastReceiver {
    private static final String TAG = MainActivity.class.getSimpleName();
    private AppExpandableListAdapter m_ListAdapter;
    private List<String> m_ServerList;
    private List<String> m_ConnectionList;
    private boolean m_NoConnections = true;

    /**
     * Ctor
     * @param activity the main activity we're working with
     * @param serverList the list of servers
     * @param connectionList the list of connections
     * @param adapter the list adapter managed by the app
     */
    public AppBroadcastReceiver(MainActivity activity, List<String> serverList,
                                List<String> connectionList, AppExpandableListAdapter adapter) {
        super();
        m_ListAdapter = adapter;
        m_ServerList = serverList;
        m_ConnectionList = connectionList;

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

        // Start with a clean slate...
        m_ServerList.clear();

        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        try {
            // Brute force unwind of the intent payload into a local display
            // string...
            JSONArray servers = (JSONArray) new JSONTokener(json).nextValue();
            StringBuilder sb = new StringBuilder();
            for (int i =0; i < servers.length(); i++) {
                JSONObject obj = servers.getJSONObject(i);
                sb.append(obj.get("protocol"));
                sb.append( ":/" );
                sb.append( obj.get("description"));

                m_ServerList.add(sb.toString());
                sb.setLength(0);
            }

        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Special case - if we didn't get anything then make sure that we
        // give the user something to look at.
        if ( m_ServerList.size() == 0 ) {
            m_ServerList.add("None");
        }

        // Force a redraw...
        m_ListAdapter.notifyDataSetChanged();
    }

    /**
     * Process the full connections list.  Usually in response to a request for all connections.
     * @param intent Intent with the list of connections
     */
    private void handleConnectionsIntent(Intent intent) {
        android.util.Log.i(TAG, "handleConnectionsIntent");

        m_ConnectionList.clear();

        // Iterate over the received connections and create a set of display strings...
        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        try {
            // Brute force unwind of the intent payload into a local display
            // string...
            JSONArray connections = (JSONArray) new JSONTokener(json).nextValue();
            for (int i =0; i < connections.length(); i++) {
                JSONObject obj = connections.getJSONObject(i);
                m_ServerList.add(obj.getString("description"));
                // TODO: When we add tx/rx counts to the list view items, pull that info here...
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Special case - if we didn't get anything then make sure that we
        // give the user something to look at.
        if ( m_ConnectionList.size() == 0 ) {
            m_ConnectionList.add("None");
            m_NoConnections = true;
        }
        else {
            // Save some state here so we know when we get individual
            // new connections if we have to clear the "None" default list value
            // or not...
            m_NoConnections = false;
        }

        // Force a redraw...
        m_ListAdapter.notifyDataSetChanged();
    }

    private void handleNewConnectionIntent(Intent intent) {
        android.util.Log.i(TAG, "handleNewConnectionIntent");

        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        try {
            // Parse the new connection...
            JSONObject connection = (JSONObject) new JSONTokener(json).nextValue();

            // Build up a display string
            // TODO: Would be prettier to do a custom list view with a protocol field
            // or icon.  Just stringing it for now...
            String displayText = getDisplayString(connection);

            // If this is our first connection then clear our placeholder item
            if (m_NoConnections == true) {
                m_ConnectionList.clear();
                m_NoConnections = false;
                m_ConnectionList.add(displayText);
            }
            else if (m_ConnectionList.contains(displayText) == false) {
                m_ConnectionList.add(displayText);
                Collections.sort(m_ConnectionList);
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Force a redraw...
        m_ListAdapter.notifyDataSetChanged();
    }

    private void handleClosedConnectionIntent(Intent intent) {
        android.util.Log.i(TAG, "handleClosedConnectionIntent");

        String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
        try {
            // Parse the new connection...
            JSONObject connection = (JSONObject) new JSONTokener(json).nextValue();

            String displayText = getDisplayString(connection);

            // Remove the string if we have it.  Always possible we can get out of
            // sync somehow...
            if (m_ConnectionList.contains(displayText) == true) {
                m_ConnectionList.remove(displayText);

                // If that was our last connection then fill in a default
                // "None" entry.
                if (m_ConnectionList.size() == 0) {
                    m_NoConnections = true;
                    m_ConnectionList.add("None");
                }
                else {
                    Collections.sort(m_ConnectionList);
                }
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Force a redraw...
        m_ListAdapter.notifyDataSetChanged();
    }

    @NonNull
    private String getDisplayString(JSONObject connection) throws JSONException {
        String description = connection.getString("description");
        String protocol = connection.getString("protocol");
        return protocol + ":/" + description;
    }

}
