package msgtools.milesengineering.msgserver.connectionmgr;

import java.lang.ref.WeakReference;
import java.nio.ByteBuffer;
import java.util.Vector;

import headers.NetworkHeader;

/**
 * Utility class for handling connection listeners...
 */

public class ConnectionListenerHelper {
    private static final Object m_Lock = new Object();
    private String m_LogTag;
    private WeakReference<IConnectionMgr>  m_Mgr;
    private Vector<IConnectionMgrListener> m_Listeners = new Vector<IConnectionMgrListener>();

    public ConnectionListenerHelper(String logTag, IConnectionMgr mgr ) {
        m_LogTag = logTag;
        m_Mgr = new WeakReference<IConnectionMgr>(mgr);
    }

    public void addListener(IConnectionMgrListener listener) {
        synchronized (m_Lock) {
            m_Listeners.add(listener);
        }
    }

    public boolean removeListener(IConnectionMgrListener listener) {
        synchronized (m_Lock) {
            return m_Listeners.remove(listener);
        }
    }

    public void onNewConnection(IConnection newConnection) {
        synchronized (m_Lock) {
            android.util.Log.i(m_LogTag, "oNewConnection(...)");
            IConnectionMgr mgr = m_Mgr.get();
            if ( mgr != null ) {
                for (IConnectionMgrListener l : m_Listeners) {
                    l.onNewConnection(mgr, newConnection);
                }
            }
        }
    }

    public void onClosedConnection(IConnection closedConnection) {
        synchronized (m_Lock) {
            android.util.Log.i(m_LogTag, "oClosedConnection(...)");
            IConnectionMgr mgr = m_Mgr.get();
            if ( mgr != null ) {
                for (IConnectionMgrListener l : m_Listeners) {
                    l.onClosedConnection(mgr, closedConnection);
                }
            }
        }
    }

    public void onMessage(IConnection srcConnection, NetworkHeader networkHeader,
                          ByteBuffer header, ByteBuffer payload) {
        synchronized (m_Lock) {
            android.util.Log.i(m_LogTag, "oMessage(...)");
            IConnectionMgr mgr = m_Mgr.get();
            if ( mgr != null ) {
                for (IConnectionMgrListener l : m_Listeners) {
                    l.onMessage(mgr, srcConnection, networkHeader, header, payload);
                }
            }
        }
    }
}
