package msgtools.milesengineering.msgserver.connectionmgr;

import java.nio.ByteBuffer;

import headers.NetworkHeader;

/**
 * Callback interface for connection events.  All callbacks are done on the connection
 * manager's thread.  Don't block for too long or traffic may be dropped.
 */
public interface IConnectionMgrListener {

    /**
     * See BaseConnectionMgr.onNewConnection
     */
    void onNewConnection(IConnectionMgr mgr, IConnection newConnection);

    /**
     * See BaseConnectionMgr.onClosedConnection
     */
    void onClosedConnection(IConnectionMgr mgr, IConnection closedConnection);

    /**
     * See BaseConnectionMgr.onMessage
     */
    void onMessage(IConnectionMgr mgr, IConnection srcConnection, NetworkHeader networkHeader,
                   ByteBuffer header, ByteBuffer payload);
}
