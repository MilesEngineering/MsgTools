package msgtools.milesengineering.msgserver.connectionmgr;

import java.nio.ByteBuffer;

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
