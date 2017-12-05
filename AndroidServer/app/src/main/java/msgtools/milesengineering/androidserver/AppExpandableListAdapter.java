package msgtools.milesengineering.androidserver;

import android.content.Context;
import android.graphics.Typeface;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Expandable list adapter for our data set.  Credit where due: Adopted from a tutorial
 * on Android hive at https://www.androidhive.info/2013/07/android-expandable-list-view-tutorial
 *
 * This class serves as a data model (and controller to some extent as it's doing formatting
 * etc.)
 */
public class AppExpandableListAdapter extends BaseExpandableListAdapter {
    private static final String TAG = AppExpandableListAdapter.class.getSimpleName();

    private Context m_Context;
    private List<String> m_ListHeaders = new ArrayList<String>(); // header titles
    private List<String> m_Servers = new ArrayList<String>();
    private List<JSONObject> m_Connections = new ArrayList<JSONObject>();

    /**
     * Utility method for connection sorting...
     */
    private class ConnectionComparator implements Comparator<JSONObject> {

        @Override
        public int compare(JSONObject o1, JSONObject o2) {
            try {
                String o1description = o1.getString("description");
                String o2description = o2.getString("description");
                return o1description.compareTo(o2description);
            }
            catch( JSONException je ) {
                je.printStackTrace();
            }

            return -1;
        }
    }

    public AppExpandableListAdapter(Context context) {
        m_Context = context;

        // Setup some hard coded headers...
        m_ListHeaders.add("Servers");
        m_ListHeaders.add("Connections");
    }

    //
    // Data Model API for making updates
    //


    /**
     * Pass in a JSON string of servers (from a broadcast intent).  This method will
     * completely overwrite any existing data in favor of the new data
     *
     * @param jsonServers JSON array of servers.
     */
    public void setServers(String jsonServers) {
        android.util.Log.i(TAG, "setServers(...)");

        // Start with a clean slate.
        m_Servers.clear();

        try {
            // Brute force unwind of the intent payload into a local display
            // string...
            JSONArray servers = (JSONArray) new JSONTokener(jsonServers).nextValue();
            for (int i =0; i < servers.length(); i++) {
                JSONObject obj = servers.getJSONObject(i);
                String displayText = String.format( "%s: %s", obj.optString("protocol", "???"),
                        obj.optString("description", "UNKNOWN"));
                m_Servers.add(displayText);
            }

        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Special case - if we didn't get anything then make sure that we
        // give the user something to look at.
        if ( m_Servers.size() == 0 ) {
            m_Servers.add("None");
        }

        // Force a redraw...
        notifyDataSetChanged();
    }

    /**
     * Set the connections en masse.  This method clears any existing connection data in favor
     * of the new array passed in.
     *
     * @param jsonConnections JSON string for an array of connetions.
     */
    public void setConnections(String jsonConnections) {
        android.util.Log.i(TAG, "setConnections(...)");

        m_Connections.clear();

        // Iterate over the received connections and create a set of display strings...
        try {
            // Brute force unwind of the intent payload into a local display
            // string...
            JSONArray connections = (JSONArray) new JSONTokener(jsonConnections).nextValue();
            for (int i =0; i < connections.length(); i++) {
                JSONObject obj = connections.getJSONObject(i);
                m_Connections.add(obj);
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Force a redraw...
        notifyDataSetChanged();
    }


    /**
     * Add a new connection to the data model and update
     * @param jsonConnection JSON string for a connection
     */
    public void addNewConnection(String jsonConnection) {
        android.util.Log.i(TAG, "addNewConnection(...)");

        try {
            // Parse the new connection...
            JSONObject connection = (JSONObject) new JSONTokener(jsonConnection).nextValue();

            if (m_Connections.contains(connection) == false) {
                m_Connections.add(connection);

                // TODO: Implement a JSON Object sort...
                m_Connections.sort(new ConnectionComparator());
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Force a redraw...
        notifyDataSetChanged();
    }

    /**
     * Remove a connection from the data model and refresh
     *
     * @param jsonConnection JSON string for a connection
     */
    public void removeClosedConnection(String jsonConnection) {
        android.util.Log.d(TAG, "removeClosedConnection(...)");
        try {
            // Parse the new connection...
            JSONObject connection = (JSONObject) new JSONTokener(jsonConnection).nextValue();

            // Remove the string if we have it.  Always possible we can get out of
            // sync somehow...
            if (m_Connections.contains(connection) == true) {
                m_Connections.remove(connection);

                if (m_Connections.size() > 1) {
                    m_Connections.sort(new ConnectionComparator());
                }
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }

        // Force a redraw...
        notifyDataSetChanged();
    }

    //
    // Expandable List Methods
    //

    @Override
    public Object getChild(int groupPosition, int childPosition) {
        android.util.Log.d(TAG, "getChild(...)");

        Object retVal = null;
        if (groupPosition == 0) {
            retVal = m_Servers.get(childPosition);
        }
        else if (groupPosition == 1) {
            retVal = m_Connections.get(childPosition);
        }

        return retVal;
    }

    @Override
    public long getChildId(int groupPosition, int childPosition) {
        android.util.Log.d(TAG, "setChildId(...)");
        return childPosition;
    }

    @Override
    public View getChildView(int groupPosition, final int childPosition,
                             boolean isLastChild, View convertView, ViewGroup parent) {
        android.util.Log.d(TAG, "getChildView(...)");

        View retVal = convertView;

        // We are supporting two separate views for servers and connections.  Thus we need to
        // behave differently according to the groupPosition
        switch(groupPosition) {
            case 0: // Servers
                if (retVal == null || retVal.getTag().equals("SERVER") == false) {
                    LayoutInflater infalInflater = (LayoutInflater) this.m_Context
                            .getSystemService(Context.LAYOUT_INFLATER_SERVICE);

                    retVal = infalInflater.inflate(R.layout.list_item, null);
                    retVal.setTag("SERVER");
                }

                // If we have no servers then respond with a none cell
                String serverText = "None";
                if (m_Servers.size() != 0)
                    serverText = (String) getChild(groupPosition, childPosition);

                TextView serverDescription = (TextView) retVal.findViewById(R.id.lblDescription);
                serverDescription.setText(serverText);

                break;
            case 1: // Connections
                if (convertView == null || retVal.getTag().equals("CONNECTION")==false) {
                    LayoutInflater infalInflater = (LayoutInflater) this.m_Context
                            .getSystemService(Context.LAYOUT_INFLATER_SERVICE);

                    retVal = infalInflater.inflate(R.layout.connection_item, null);
                    retVal.setTag("CONNECTION");
                }

                String descriptionText = "None";
                TextView textView;

                if (m_Connections.size() != 0) {
                    JSONObject connection = (JSONObject) getChild(groupPosition, childPosition);
                    descriptionText = String.format( "%s: %s", connection.optString( "protocol", "???"),
                            connection.optString("description", "UNKNOWN") );

                    textView = (TextView) retVal.findViewById(R.id.lblTx);
                    String countText = "TX " + connection.optString("sentCount", "--");
                    textView.setText(countText);

                    textView = (TextView) retVal.findViewById(R.id.lblRx);
                    countText = "RX " + connection.optString("recvCount", "--");
                    textView.setText(countText);
                }

                // Set the description last.
                textView = (TextView) retVal.findViewById(R.id.lblDescription);
                textView.setText(descriptionText);

                break;
            default:
                android.util.Log.e(TAG, "Unknown group requested");
        }

        return retVal;
    }

    @Override
    public int getChildrenCount(int groupPosition) {
        android.util.Log.d(TAG, "getChildrenCount(...)");

        int retVal = 0;
        switch(groupPosition) {
            case 0: // Servers
                retVal = m_Servers.size();
                break;
            case 1: // Connections
                retVal = m_Connections.size();
                break;
        }

        // If we have no items return 1 because we want to fill in with a default "None"
        // row entry...
        retVal = retVal == 0 ? 1 : retVal;

        return retVal;
    }

    @Override
    public Object getGroup(int groupPosition) {
        android.util.Log.d(TAG, "getGroup(...)");
        return m_ListHeaders.get(groupPosition);
    }

    @Override
    public int getGroupCount() {
        android.util.Log.d(TAG, "getGroupCount(...)");
        return m_ListHeaders.size();
    }

    @Override
    public long getGroupId(int groupPosition) {
        android.util.Log.d(TAG, "getGroupId(...)");
        return groupPosition;
    }

    @Override
    public View getGroupView(int groupPosition, boolean isExpanded,
                             View convertView, ViewGroup parent) {
        android.util.Log.d(TAG, "getGroupView(...)");

        String headerTitle = (String)getGroup(groupPosition);
        if (convertView == null) {
            LayoutInflater infalInflater = (LayoutInflater) this.m_Context
                    .getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            convertView = infalInflater.inflate(R.layout.list_header, null);
        }

        TextView lblListHeader = (TextView) convertView
                .findViewById(R.id.list_header);
        lblListHeader.setTypeface(null, Typeface.BOLD);
        lblListHeader.setText(headerTitle);

        return convertView;
    }

    @Override
    public boolean hasStableIds() {
        android.util.Log.d(TAG, "hasStableIds(...)");
        return false;
    }

    @Override
    public boolean isChildSelectable(int groupPosition, int childPosition) {
        android.util.Log.d(TAG, "isChildSelectable(...)");
        return false;
    }
}