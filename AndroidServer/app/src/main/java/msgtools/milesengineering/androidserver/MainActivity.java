package msgtools.milesengineering.androidserver;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.inputmethod.EditorInfo;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.ExpandableListView;
import android.widget.TextView;
import android.widget.ToggleButton;

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

    private MsgServerServiceAPI m_MsgServerAPI;
    private BroadcastReceiver m_BroadcastReceiver;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        android.util.Log.i(TAG, "onCreate(...)");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar)findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

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
                filename = timestampString;

            String msgVersion = m_MsgVersionEditText.getText().toString();

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
