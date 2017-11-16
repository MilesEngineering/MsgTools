package msgtools.milesengineering.androidserver;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;

import msgtools.milesengineering.msgserver.MsgServerService;
import msgtools.milesengineering.msgserver.MsgServerServiceAPI;

public class MainActivity extends AppCompatActivity implements ServiceConnection {
    private static final String TAG = MainActivity.class.getSimpleName();

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
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        android.util.Log.i(TAG, "onCreate(...)");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        FloatingActionButton fab = (FloatingActionButton) findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Snackbar.make(view, "Replace with your own action", Snackbar.LENGTH_LONG)
                        .setAction("Action", null).show();
            }
        });

        // Instantiate a broadcast receiver.  This class automatically
        // registers, and invokes calls on the activity.  Could
        // hand an interface in, instead of the MainActivity to make this
        // more portable but it's a small amount of code and others can just copy
        // and paste...

        m_BroadcastReceiver = new AppBroadcastReceiver(this);

        // Register to receive intents from the MsgServer for UI updates...
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(MsgServerService.INTENT_ACTION);
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
}
