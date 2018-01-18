package msgtools.milesengineering.androidserver;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.IBinder;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.inputmethod.EditorInfo;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.ExpandableListView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ToggleButton;

import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;

import msgtools.milesengineering.msgserver.MsgServerService;
import msgtools.milesengineering.msgserver.MsgServerServiceAPI;

public class MainActivity extends AppCompatActivity implements ServiceConnection,
        CompoundButton.OnCheckedChangeListener, TextView.OnEditorActionListener
{
    private static final String TAG = MainActivity.class.getSimpleName();

    AppExpandableListAdapter m_ListAdapter;
    ExpandableListView m_ListView;
    EditText m_FilenameEditText;
    EditText m_MsgVersionEditText;
    ToggleButton m_LoggingButton;

    String m_LastBaseFilename = "";
    String m_LastMsgVersion = "";

    private MsgServerServiceAPI m_MsgServerAPI;
    private BroadcastReceiver m_BroadcastReceiver;

    //
    // Intent handling from our service
    //
    /**
     * Simple utility class - designed to parse and invoke methods on
     * the MainActivity.  It acts as a sort of proxy data model for the list
     */
    class AppBroadcastReceiver extends BroadcastReceiver {
        private AppExpandableListAdapter m_ListAdapter;
        private MainActivity m_Activity;

        /**
         * Ctor
         * @param activity the main activity we're working with
         * @param adapter the list adapter managed by the app
         */
        public AppBroadcastReceiver(MainActivity activity, AppExpandableListAdapter adapter) {
            super();
            m_ListAdapter = adapter;
            m_Activity = activity;

            // Register to receive intents from the MsgServer for UI updates...
            // Add new intents here...
            IntentFilter intentFilter = new IntentFilter();
            intentFilter.addAction(MsgServerService.INTENT_SEND_SERVERS);
            intentFilter.addAction(MsgServerService.INTENT_SEND_CONNECTIONS);
            intentFilter.addAction(MsgServerService.INTENT_SEND_NEW_CONNECTION);
            intentFilter.addAction(MsgServerService.INTENT_SEND_CLOSED_CONNECTION);
            intentFilter.addAction(MsgServerService.INTENT_SEND_LOGGING_STATUS);
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
            android.util.Log.d(TAG, "AppBroadcastReceiver::onReceive(...)");
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
            else if (intent.getAction().equals(MsgServerService.INTENT_SEND_LOGGING_STATUS)) {
                handleLoggingStatusIntent(intent);
            }
        }

        /**
         * Process an updated server list from the server...
         * @param intent the intent to handle...
         */
        private void handleServersIntent(Intent intent) {
            android.util.Log.d(TAG, "handleServersIntent");
            String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);
            m_ListAdapter.setServers(json);
        }

        /**
         * Process the full connections list.  Usually in response to a request for all connections.
         * @param intent Intent with the list of connections
         */
        private void handleConnectionsIntent(Intent intent) {
            android.util.Log.d(TAG, "handleConnectionsIntent");
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

        private void handleLoggingStatusIntent(Intent intent) {
            android.util.Log.i(TAG, "handleLoggingStatusIntent");

            String json = (String) intent.getExtras().get(Intent.EXTRA_TEXT);

            try {
                // Update our UI elements to match
                JSONObject jsonObj = (JSONObject) new JSONTokener(json).nextValue();

                m_LoggingButton.setOnCheckedChangeListener(null);   // So we don't get into a callback loop
                m_LoggingButton.setChecked(jsonObj.getBoolean("enabled"));

                m_FilenameEditText.setText(jsonObj.optString("filename", m_LastBaseFilename));
                m_MsgVersionEditText.setText(jsonObj.optString("msgVersion", m_LastMsgVersion ));

                // If we have an error then show a toast
                String errorMsg = jsonObj.optString("error", null);
                if (errorMsg != null) {
                    Toast toast = Toast.makeText(m_Activity, errorMsg, Toast.LENGTH_LONG);
                    toast.setGravity(Gravity.TOP, 0, 0);
                    toast.show();
                }
            }
            catch(JSONException je) {
                je.printStackTrace();
            }
            finally {
                // Make sure we get user updates!
                m_LoggingButton.setOnCheckedChangeListener(m_Activity);

                // If we're no longer checked then re-enable our text edits
                if( m_LoggingButton.isChecked() == false ) {
                    m_FilenameEditText.setEnabled(true);
                    m_MsgVersionEditText.setEnabled(true);
                }
            }
        }
    }



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        android.util.Log.i(TAG, "onCreate(...)");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar)findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        // For logging etc...
        isStoragePermissionGranted();

        // Little bit of a hack here - the service should be creating this in MessageLogger, but for
        // some reason the mkdirs there silently fails.  Rather than dump time sorting it out
        // just rolling with this for the moment.
        File logDir = new File(Environment.getExternalStorageDirectory().getAbsolutePath(),
                MsgServerService.LOG_DIRECTORY);
        if (logDir.exists() == false)
            if (logDir.mkdirs() == false)
                android.util.Log.e(TAG, "Unable to create storage folder!");

        // Setup our list view
        m_ListView = (ExpandableListView)findViewById(R.id.listview);
        setupExpandableList();

        // Register for events from our logging widgets
        m_FilenameEditText = (EditText)findViewById(R.id.editTextFilenaame);
        m_MsgVersionEditText = (EditText)findViewById(R.id.editTextVersion);
        m_LoggingButton = (ToggleButton)findViewById(R.id.toggleButton);

        m_LoggingButton.setOnCheckedChangeListener(this);

        // Instantiate a broadcast receiver.  This is where all the service intent
        // handling, and list updating happens.
        m_BroadcastReceiver = new AppBroadcastReceiver(this, m_ListAdapter);

        // Start the Server service
        Intent intent = new Intent(this, MsgServerService.class);
        startService(intent);

        // Now bind to it so we can access the service API to drive our UI
        bindService(intent, this, BIND_IMPORTANT);
    }

    private  boolean isStoragePermissionGranted() {
        if (Build.VERSION.SDK_INT >= 23) {
            if (checkSelfPermission(android.Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_GRANTED) {
                return true;
            } else {
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
                return false;
            }
        }
        else { //permission is automatically granted on sdk<23 upon installation
            return true;
        }
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

            // Also ask for a list of all active connections
            m_MsgServerAPI.requestConnections();
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
     * Preparing the list
     */
    private void setupExpandableList() {
        m_ListAdapter = new AppExpandableListAdapter(this);
        m_ListView.setAdapter(m_ListAdapter);

        // Pre-expand
        m_ListView.expandGroup(0);
        m_ListView.expandGroup(1);
    }

    //
    // UI Event handling - primarily logging management...
    //
    @Override
    public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
        if ( isChecked == false ) {
            m_MsgServerAPI.stopLogging();

            m_FilenameEditText.setEnabled(true);
            m_MsgVersionEditText.setEnabled(true);
            m_FilenameEditText.setText(m_LastBaseFilename);
        }
        else {
            // Build up a filename with date and time info appended
            // It would be easier to use the Instant class but that isn't
            // available until API 26 and we want to support older devices.
            Date now = new Date();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'");
            sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
            String timestampString = sdf.format(now);

            String filename = m_FilenameEditText.getText().toString().trim();
            m_LastBaseFilename = filename;

            if ( filename.length() > 0 )
                filename = String.format("%s_%s.log", filename, timestampString);
            else
                filename = String.format("%s.log", timestampString);

            String msgVersion = m_MsgVersionEditText.getText().toString();
            m_LastMsgVersion = msgVersion;

            m_FilenameEditText.setEnabled(false);
            m_MsgVersionEditText.setEnabled(false);
            m_FilenameEditText.setText(filename);   // Let the user know the full filename we're logging to

            m_MsgServerAPI.startLogging(filename, msgVersion);
        }
    }

    @Override
    public boolean onEditorAction(TextView v, int actionId, KeyEvent event) {
        if (actionId == EditorInfo.IME_ACTION_DONE) {
            // Just hide the keyboard if the user hits done
            v.clearFocus();
            return true;
        }
        return false;
    }
}
