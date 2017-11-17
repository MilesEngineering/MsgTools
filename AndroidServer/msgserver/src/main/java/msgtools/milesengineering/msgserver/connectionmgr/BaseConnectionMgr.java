package msgtools.milesengineering.msgserver.connectionmgr;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;

/**
 * This class represents a BaseConnectionMgr that abstracts concepts like
 * Bluetooth, Websocket, and TCP type services that watch for new data connections.
 */

public abstract class BaseConnectionMgr extends Thread {
    private static final String TAG = BaseConnectionMgr.class.getSimpleName();

    private Object m_Lock = new Object();   // Used as a private sync object for thread safety
    private ArrayList<IConnectionMgrListener> m_Listeners = new ArrayList<IConnectionMgrListener>();
    private ArrayList<IConnection> m_ActiveConnections = new ArrayList<IConnection>();

    /**
     * Callback interface for connection events.  All callbacks are done on the connection
     * manager's thread.  Don't block for too long or traffic may be dropped.
     */
    public interface IConnectionMgrListener {

        /**
         * See BaseConnectionMgr.onNewConnection
         */
        void onNewConnection(BaseConnectionMgr mgr, IConnection newConnection);

        /**
         * See BaseConnectionMgr.onClosedConnection
         */
        void onClosedConnection(BaseConnectionMgr mgr, IConnection closedConnection);

        /**
         * See BaseConnectionMgr.onMessage
         */
        void onMessage(BaseConnectionMgr mgr, IConnection srcConnection, long msgId, ByteBuffer payload);
    }

    /**
     * Connection interface, that represents a connection to a message source/sink
     * Your implementation MUST be threadsafe with respect to this interface.
     */
    public interface IConnection {

        /**
         * Send a  message on this connection. The message will be converted
         * to use a header appropriate to it's underlying transport before sending.
         *
         * @param msgId MsgTools header message ID
         * @param payloadBuff Data payload for the message.
         * @return true if the message was sent, else false
         */
        boolean sendMessage( long msgId, ByteBuffer payloadBuff );

        /**
         * Get the total number of messages sent
         *
         * @return int of total messages sent
         */
        int getMessagesSent();

        /**
         * Get the total number of messages received
         *
         * @return int total messages received
         */
        int getMessagesReceived();

        /**
         * Close the connection.
         */
        void close() throws IOException;
    }

    private BaseConnectionMgr() {}

    /**
     * Base constructor
     * @param listener Callback interface for connection events
     */
    public BaseConnectionMgr(IConnectionMgrListener listener) {
        m_Listeners.add( listener );
    }

    /**
     * Add a new listener to our callback list.  Listeners are invoked on
     * the ConnectionManager's thread and should be threadsafe and not hold up
     * exeuction for too long.
     *
     * @param listener Listener to add to the list
     */
    public void addListener( IConnectionMgrListener listener ) {
        synchronized(m_Lock) {
            m_Listeners.add(listener);
        }
    }

    /**
     * Remove a listener from the list
     * @param listener Listener to remove
     * @return true if the listener was removed, else false
     */
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

    /**
     * Stop monitoring and close all active connections.
     *
     */
    public void requestHalt() {
        android.util.Log.i(TAG, "requestHalt()");
        m_HaltPending = true;
    }

    /**
     * Check to see if a halt request is pending...use Thread.getState or isAlive
     * to confirm when the thread is done.
     * @return true if halt is pending, else false.
     */
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
