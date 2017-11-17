package msgtools.milesengineering.msgserver.connectionmgr;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;

/**
 * This class represents a BaseConnectionMgr that abstracts concepts like
 * Bluetooth, Websocket, and TCP type services that watch for new data connections.
 */

public abstract class BaseConnectionMgr extends Thread implements IConnectionMgr {
    private static final String TAG = BaseConnectionMgr.class.getSimpleName();

    private Object m_Lock = new Object();   // Used as a private sync object for thread safety
    private ArrayList<IConnectionMgrListener> m_Listeners = new ArrayList<IConnectionMgrListener>();
    private ArrayList<IConnection> m_ActiveConnections = new ArrayList<IConnection>();

    private BaseConnectionMgr() {}

    /**
     * Base constructor
     * @param listener Callback interface for connection events
     */
    public BaseConnectionMgr(IConnectionMgrListener listener) {
        m_Listeners.add( listener );
    }

    @Override
    public void addListener( IConnectionMgrListener listener ) {
        synchronized(m_Lock) {
            m_Listeners.add(listener);
        }
    }

    @Override
    public boolean removeListener( IConnectionMgrListener listener ) {
        synchronized (m_Lock) {
            return m_Listeners.remove(listener);
        }
    }

    /**
     * Main execution loop from Thread.  See setup, execute, and cleanup for more details.
     */
    @Override
    public final void run() {
        android.util.Log.i(TAG, "run()");
        try {
            android.util.Log.i(TAG, "setup()");
            setup();

            while(haltPending() == false) {
                execute();
            }

            android.util.Log.i(TAG, "cleanup()");
            cleanup();
        } catch(IOException ioe) {
            android.util.Log.w(TAG, "Exception in Manager loop");
            android.util.Log.w(TAG, ioe.toString());
        }

        // Drop all listeners and close all connections
        android.util.Log.i(TAG, "Clearing listeners and closing connections...");
        synchronized (m_Lock) {
            m_Listeners.clear();
            for( IConnection c : m_ActiveConnections ) {
                try {
                    c.close();
                } catch(Exception e) {
                    // Don't care...
                }
            }

            m_ActiveConnections.clear();
        }
    }

    private boolean m_HaltPending;

    @Override
    public void requestHalt() {
        android.util.Log.i(TAG, "requestHalt()");
        m_HaltPending = true;
    }

    @Override
    public boolean haltPending() {
        return m_HaltPending;
    }

    /**
     * Get the sync object use to sycnrhonize methods
     *
     * @return Object instance used to sync on
     */
    protected Object getLock() {
        return m_Lock;
    }

    /**
     * Override this method to do any pre-execution setup.  For instance
     * setup server sockets, managers, or whatever...
     *
     * The base implementation does nothing.
     */
    protected void setup() throws IOException {

    }

    /**
     * Override and place your main thread execution method here.  This method should always return
     * so the base class can test for halt requests etc.  You're free to block, but
     * periodically return.
     */
    protected abstract void execute() throws IOException;

    /**
     * Close any open resources.  The BaseConnectionMgr
     * will close all connections after execution of this method
     * returns.  The base implementation does nothing.
     */
    protected void cleanup() {

    }

    /**
     * Adds a new tracked connection and notifies all listeners
     * a new connection has been created.
     *
     * @param newConnection The new connection
     */
    protected void onNewConnection(IConnection newConnection) {
        android.util.Log.i(TAG, "onNewConnection(...)");
        synchronized(m_Lock) {
            for( IConnectionMgrListener l : m_Listeners ) {
                try {
                    l.onNewConnection(this, newConnection);
                }
                catch( Exception e ) {
                    android.util.Log.w(TAG, e.toString() );
                }
            }
        }
    }

    /**
     * Removes the connection from the list of tracked connections and
     * notifies all listeners of the closure.
     *
     * @param closedConnection The connection that was closed.
     */
    protected void onClosedConnection(IConnection closedConnection) {
        android.util.Log.i(TAG, "onClosedConnection(...)");
        synchronized(m_Lock) {
            for( IConnectionMgrListener l : m_Listeners ) {
                try {
                    l.onClosedConnection(this, closedConnection);
                }
                catch( Exception e ) {
                    android.util.Log.w(TAG, e.toString() );
                }
            }
        }
    }

    /**
     * Invoke this method when a new message has been received.  All registered listeners
     * will be notified of the new message.
     * @param srcConnection The connection that sourced the message
     * @param msgId The message ID for the message
     * @param payloadBuff  The data payload for the message
     */
    protected void onMessage(IConnection srcConnection, long msgId, ByteBuffer payloadBuff) {
        android.util.Log.i(TAG, "onMessage(...)");
        synchronized(m_Lock) {
            for( IConnectionMgrListener l : m_Listeners ) {
                try {
                    l.onMessage(this, srcConnection, msgId, payloadBuff);
                }
                catch( Exception e ) {
                    android.util.Log.w(TAG, e.toString() );
                }
            }
        }
    }
}
