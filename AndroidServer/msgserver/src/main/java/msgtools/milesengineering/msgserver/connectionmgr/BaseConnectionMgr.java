package msgtools.milesengineering.msgserver.connectionmgr;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.HashSet;

import headers.NetworkHeader;

/**
 * This class represents a BaseConnectionMgr that abstracts concepts like
 * Bluetooth, Websocket, and TCP type services that watch for new data connections.
 */

public abstract class BaseConnectionMgr extends Thread implements IConnectionMgr {
    private static final String TAG = BaseConnectionMgr.class.getSimpleName();

    private Object m_Lock = new Object();   // Used as a private sync object for thread safety
    private ConnectionListenerHelper m_Listeners;
    private HashSet<IConnection> m_ActiveConnections = new HashSet<IConnection>();

    private BaseConnectionMgr() {
        m_Listeners = new ConnectionListenerHelper(TAG, this);
    }

    /**
     * Base constructor
     *
     * @param listener Callback interface for connection events
     */
    public BaseConnectionMgr(IConnectionMgrListener listener) {
        m_Listeners = new ConnectionListenerHelper(TAG, this);
        m_Listeners.addListener(listener);
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

            while (haltPending() == false) {
                execute();
            }

            android.util.Log.i(TAG, "cleanup()");
            cleanup();
        } catch (IOException ioe) {
            android.util.Log.w(TAG, "Exception in Manager loop");
            android.util.Log.w(TAG, ioe.toString());
        }

        // Drop all listeners and close all connections
        android.util.Log.i(TAG, "Clearing listeners and closing connections...");
        synchronized (m_Lock) {
            for (IConnection c : m_ActiveConnections) {
                try {
                    c.close();
                } catch (Exception e) {
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
     * Get the listener helper used to broadcast connection events.
     *
     * @return ConnectionListenerHelper of listeners
     */
    protected ConnectionListenerHelper getListeners() { return m_Listeners; }

    /**
     * Override this method to do any pre-execution setup.  For instance
     * setup server sockets, managers, or whatever...
     * <p>
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

    //
    // Listener handlers
    //

    @Override
    public void addListener(IConnectionMgrListener listener) {
        m_Listeners.addListener(listener);
    }

    @Override
    public boolean removeListener(IConnectionMgrListener listener) {
        return m_Listeners.removeListener(listener);
    }

    @Override
    public abstract String getProtocol();

    @Override
    public abstract String getDescription();

    //
    // Convenience methods for invoking listeners
    //
    protected final void onNewConnection(IConnection newConnection) {
        synchronized (m_Lock) {
            m_Listeners.onNewConnection(newConnection);
            addConnection(newConnection);
        }
    }

    protected final void onClosedConnection(IConnection closedConnection) {
        synchronized (m_Lock) {
            m_Listeners.onClosedConnection(closedConnection);
            removeConnection(closedConnection);
        }
    }

    protected final void onMessage(IConnection srcConnection, NetworkHeader networkHeader,
                                   ByteBuffer hdrBuff, ByteBuffer payloadBuff) {
        synchronized (m_Lock) {
            m_Listeners.onMessage(srcConnection, networkHeader, hdrBuff, payloadBuff);
        }
    }

    /**
     * Add a connection to the list of connections being tracked.  Doing so will
     * automatically close them when the connection manager is halted.  Invoking
     * onNewConnection will automatically add the connection to the list for you.
     *
     * @param connection connection to add
     */
    protected final void addConnection(IConnection connection) {
        synchronized (m_Lock) {
            m_ActiveConnections.add(connection);
        }
    }

    /**
     * Remove a connection from the list of connections.  onClosedConnection will
     * automatically remove the connection from the list as well.
     *
     * @param connection connection to remove
     */
    protected final void removeConnection(IConnection connection) {
        synchronized (m_Lock) {
            m_ActiveConnections.remove(connection);
        }
    }
}
