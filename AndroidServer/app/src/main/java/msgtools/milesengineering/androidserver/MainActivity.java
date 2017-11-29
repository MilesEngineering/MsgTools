package msgtools.milesengineering.androidserver;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.ExpandableListView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

import msgtools.milesengineering.msgserver.MsgServerService;
import msgtools.milesengineering.msgserver.MsgServerServiceAPI;

public class MainActivity extends AppCompatActivity implements ServiceConnection {
    private static final String TAG = MainActivity.class.getSimpleName();

    AppExpandableListAdapter m_ListAdapter;
    ExpandableListView m_ListView;

    // Our data model of servers and connections
    List<String> m_Servers = new ArrayList<String>();
    List<String> m_Connections = new ArrayList<String>();

    private MsgServerServiceAPI m_MsgServerAPI;
    private BroadcastReceiver m_BroadcastReceiver;

    /**
     * Simple utility class - designed to parse and invoke methods on
     * the MainActivity
     */
    private class AppBroadcastReceiver extends BroadcastReceiver {
        private MainActivity m_MainActivity;

        public AppBroadcastReceiver(MainActivity activity) {
            super();
            m_MainActivity = activity;
        }

        @Override
        public void onReceive(final Context context, final Intent intent) {
            android.util.Log.i(TAG, "AppBroadcastReceiver::onReceive(...)");
            if (intent.getAction() == MsgServerService.INTENT_SEND_SERVERS) {
                String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
                try {
                    // Brute force unwind of the intent payload into a local dispay
                    // string...
                    JSONArray servers = (JSONArray) new JSONTokener(json).nextValue();
                    StringBuilder sb = new StringBuilder();
                    for (int i =0; i < servers.length(); i++) {
                        JSONObject obj = servers.getJSONObject(i);
                        sb.append(obj.get("protocol"));
                        sb.append( ":/" );
                        sb.append( obj.get("description"));

                        m_Servers.add(sb.toString());
                        sb.setLength(0);
                    }

                    // Force a redraw...
                    m_ListAdapter.notifyDataSetChanged();
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        android.util.Log.i(TAG, "onCreate(...)");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // Setup our list view
        m_ListView = (ExpandableListView) findViewById(R.id.listview);
        prepareList();

        // Instantiate a broadcast receiver.  This class automatically
        // registers, and invokes calls on the activity.  Could
        // hand an interface in, instead of the MainActivity to make this
        // more portable but it's a small amount of code and others can just copy
        // and paste...

        m_BroadcastReceiver = new AppBroadcastReceiver(this);

        // Register to receive intents from the MsgServer for UI updates...
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(MsgServerService.INTENT_SEND_SERVERS);
        registerReceiver(m_BroadcastReceiver, intentFilter);

        // Start the Server service
        Intent intent = new Intent(this, MsgServerService.class);
        startService(intent);

        // Now bind to it so we can access the service API to drive our UI
        bindService(intent, this, BIND_IMPORTANT);
    }

    @Override
    protected void onDestroy() {
        android.util.Log.i(TAG, "onDestroy()");

        // Stop handling intents and Unbind from the message service...
        unregisterReceiver(m_BroadcastReceiver);
        m_BroadcastReceiver = null;
        unbindService(this);

        super.onDestroy();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    //
    // ServiceConnection methods...
    //

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        android.util.Log.i(TAG, "onServiceConnected(...)");

        if ( m_MsgServerAPI == null ) {
            m_MsgServerAPI = new MsgServerServiceAPI(service);

            // Immediately ask for all available servers
            // From here we're going to assume the list is static...
            m_MsgServerAPI.requestServers();
        }
        else {
            android.util.Log.e(TAG, "Unexpected service connection!");
        }
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {
        android.util.Log.i(TAG, "onServiceDisconnected(...)");
        m_MsgServerAPI = null;
    }

    @Override
    public void onBindingDied(ComponentName name) {
        android.util.Log.i(TAG, "onBindingDied(...)");
        // TODO: Fill in what we need, if anything.
    }

    /*
     * Preparing the list data
     */
    private void prepareList() {
        List<String> listHeaders;
        HashMap<String, List<String>> listData;

        listHeaders = new ArrayList<String>();
        listData = new HashMap<String, List<String>>();

        // Setup headers
        listHeaders.add("Servers");
        listHeaders.add("Connections");

        listData.put(listHeaders.get(0), m_Servers); // Header, Child data
        listData.put(listHeaders.get(1), m_Connections);

        m_ListAdapter = new AppExpandableListAdapter(this, listHeaders, listData);
        m_ListView.setAdapter(m_ListAdapter);

        // Pre-expand
        m_ListView.expandGroup(0);
        m_ListView.expandGroup(1);
    }
}
