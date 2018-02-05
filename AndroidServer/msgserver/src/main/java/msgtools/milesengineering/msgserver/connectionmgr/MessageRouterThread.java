package msgtools.milesengineering.msgserver.connectionmgr;

import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import Network.Connect;
import Network.LogStatus;
import Network.MaskedSubscription;
import Network.PrivateSubscriptionList;
import Network.QueryLog;
import Network.StartLog;
import Network.StopLog;
import Network.SubscriptionList;
import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.MessageLogger;

/**
 * This thread manages a queue of messages, dispatching them to various clients
 * and logs.  This is done to avoid blocking sending threads with multiple registered
 * receivers and logging.  We found that Bluetooth is fairly sensitive to receive delays
 * and back pressure on the incoming buffers.
 */

public class MessageRouterThread extends Thread implements IConnectionMgrListener {
    private final static String TAG = MessageRouterThread.class.getSimpleName();
    private final int POLL_TIMEOUT = 1;     // Seconds to wait for a message before checking halt requests
    private boolean m_HaltRequested;
    private boolean m_MsgsSent;
    private MessageLogger m_MsgLogger;
    private int m_HighWaterCount = 0;

    private ConcurrentHashMap<IConnection,IConnection> m_Connections =
            new ConcurrentHashMap<IConnection,IConnection>();
    private LinkedBlockingQueue<Message> m_BlockingQueue = new LinkedBlockingQueue<Message>();

    private class Message {
        public Message( IConnectionMgr mgr, IConnection srcConnection, NetworkHeader header,
                        ByteBuffer hdrBuf, ByteBuffer payloadBuf ) {
            this.mgr = mgr;
            this.src = srcConnection;
            this.hdr = header;
            this.hdrBuf = hdrBuf;
            this.pldBuf = payloadBuf;
        }

        public IConnectionMgr mgr;
        public IConnection src;
        public NetworkHeader hdr;
        public ByteBuffer hdrBuf;
        public ByteBuffer pldBuf;
    }

    public MessageRouterThread( MessageLogger logger ) {
        android.util.Log.d(TAG, "ctor");
        setName(TAG);
        m_MsgLogger = logger;
    }

    /**
     * Check if messages have been sent.  The act of making this
     * request will reset the sent flag.  This method is not 100%
     * threadsafe for performance reasons - you may periodically
     * miss a valid sent state if the routing thread updates the state
     * after.
     *
     * @return true if messages have been sent since the last time this method was called
     */
    public boolean messagesSent() {
        boolean retVal = m_MsgsSent;
        m_MsgsSent = false;
        return retVal;
    }

    /**
     * Ask the thread to shutdown.  Try this before you go killing anything.  We should
     * take no more than 2 seconds to shutdown.
     */
    public void requestHalt() {
        m_HaltRequested = true;
    }

    @Override
    public void run() {
        try {
            while (m_HaltRequested == false) {
                Message msg = m_BlockingQueue.poll(POLL_TIMEOUT, TimeUnit.SECONDS);
                if (msg != null) {
                    try {
                        // Check to see if this is a special purpose message (Start/Stop Log, LogStatus, etc)
                        // and handle the message as appropriate.  Don't route these messages out
                        int msgId = msg.hdr.GetMessageID();
                        switch (msgId) {
                            case StartLog.MSG_ID:
                                startLogging(msg);
                                break;

                            case StopLog.MSG_ID:
                                stopLogging(msg.src);
                                break;

                            case QueryLog.MSG_ID:
                                sendLogStatus(msg.src);
                                break;

                            case LogStatus.MSG_ID:
                            case Connect.MSG_ID:
                            case MaskedSubscription.MSG_ID:
                            case SubscriptionList.MSG_ID:
                            case PrivateSubscriptionList.MSG_ID:
                                // Unsupported at present
                                break;

                            default:
                                routeMessage(msg);

                                m_MsgLogger.log(msg.hdrBuf, msg.pldBuf);
                        }
                    }
                    catch(Exception e) {
                        android.util.Log.w(TAG, "Exception in routing thread");
                        android.util.Log.w(TAG, e.getMessage());
                        android.util.Log.w(TAG, e.getStackTrace().toString());
                    }
                }
            }
        }
        catch(InterruptedException ie) {
            android.util.Log.w(TAG, "Routing thread interrupted. Exiting.");
        }
    }

    private void routeMessage(Message msg) {
        for (IConnection c : m_Connections.values()) {
            try {
                // Don't echo messages back to the sender
                if (c != msg.src ) {
                    if (c.sendMessage(msg.hdr, msg.hdrBuf, msg.pldBuf) == false) {
                        android.util.Log.w(TAG, "Message not sent by connection: " +
                                c.getDescription());
                    }
                }
            } catch (Exception e) {
                android.util.Log.w(TAG, "Exception sending message on connection: " +
                        c.getDescription());
                android.util.Log.w(TAG, e.toString());
            }
        }

        m_MsgsSent = true;
    }

    private void startLogging(Message msg) {
        android.util.Log.d(TAG, "startLogging");
        StartLog startMsg = new StartLog(msg.hdrBuf, msg.pldBuf);
        StringBuilder sb = new StringBuilder();

        for(int i = 0; i < StartLog.LogFileNameFieldInfo.count; i++) {
            char nextChar = (char)startMsg.GetLogFileName(i);
            if ( nextChar != 0x0 )
                sb.append( nextChar );
            else
                break;
        }

        String logFilename = sb.toString();

        // No filename - no problem - just use the current time
        if (logFilename.length() == 0 ) {
            Date now = new Date();
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'");
            sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
            String timestampString = sdf.format(now);

            logFilename = String.format("%s.log", timestampString);
        }

        if ( logFilename.length() > 0)
            m_MsgLogger.startLogging(logFilename, "");

        sendLogStatus(msg.src);
    }

    private void stopLogging(IConnection srcConnection) {
        android.util.Log.d(TAG, "stopLogging");
        m_MsgLogger.stopLogging();
        sendLogStatus(srcConnection);
    }

    private void sendLogStatus(IConnection destination) {
        android.util.Log.d(TAG, "sendLogStatus");
        LogStatus status = new LogStatus();
        MessageLogger.LogStatus logStatus = m_MsgLogger.getStatus();

        if ( logStatus.enabled == true ) {
            status.SetLogOpen( (short)1 );

            byte[] logFilename = logStatus.filename.getBytes();
            for (int i = 0; i < logFilename.length; i++)
                status.SetLogFileName(logFilename[i], i);
            status.SetLogFileType((short) LogStatus.LogFileTypes.Binary.intValue());
        }
        else
            status.SetLogOpen( (short)0 );

        destination.sendMessage( status.GetHeader(), status.GetHeader().GetBuffer(), status.GetBuffer() );
    }

    @Override
    public void onNewConnection(IConnectionMgr mgr, IConnection newConnection) {
        if (m_Connections.put(newConnection, newConnection) != null)
            android.util.Log.w(TAG, "Received a duplicate new connection event");
    }

    @Override
    public void onClosedConnection(IConnectionMgr mgr, IConnection closedConnection) {
        if ( m_Connections.remove(closedConnection) != null )
            android.util.Log.w(TAG, "Attempted to remove a closed connection that is not being tracked");
    }

    @Override
    public void onMessage(IConnectionMgr mgr, IConnection srcConnection, NetworkHeader networkHeader, ByteBuffer header, ByteBuffer payload) {
        // Create a new message and enqueue it for processing
        Message newMsg = new Message(mgr, srcConnection, networkHeader, header, payload );
        if ( m_BlockingQueue.offer(newMsg) == false )
            android.util.Log.e(TAG, "Msg queue overflow!!!");

        int queueSize = m_BlockingQueue.size();
        if ( queueSize > 100 && m_HighWaterCount <= 100 ) {
            android.util.Log.w(TAG, "MsgQueue over 100");
        }

        if (queueSize > m_HighWaterCount ) {
            android.util.Log.i(TAG, "New queue high water count: " + m_HighWaterCount);
            m_HighWaterCount = queueSize;
        }

    }
}
