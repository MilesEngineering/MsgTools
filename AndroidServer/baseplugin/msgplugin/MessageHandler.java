package msgplugin;

import headers.BluetoothHeader;
import headers.NetworkHeader;
import msgtools.milesengineering.msgserver.connectionmgr.IConnection;
import test.BandwidthTest;

import java.nio.ByteBuffer;
import java.util.Date;


/**
 * This is a base MessageHandler that allows you to customize connection and message behavior within
 * AndroidServer.  For instance conversion of Bluetooth and Network headers, or specialized handling
 * of certain messages before they are sent or routed.
 */

public class MessageHandler {
    private static MessageHandler m_TheInstance;

    /**
     * Get the instance of the message handler in use.  This is a Singleton so
     * all messages work to a common time stamp.  Important for bandwidth tester.
     *
     * @return The instance of the MessageHandler
     */
    public static MessageHandler getInstance() {
        if (m_TheInstance == null) {
            m_TheInstance = new MessageHandler(new Date().getTime()); // To keep time within 32 bits we'll send a delta from server start
        }

        return m_TheInstance;
    }

    private MessageHandler(long baseTime) {
        m_BaseTime = baseTime;
    }
    protected long m_BaseTime;

    /**
     * Get the base time for the message handler
     *
     * @return long which is ms since 1970
     * @see java.util.Date#getTime()
     */
    public long getBaseTime() { return m_BaseTime; }

    /**
     * Called by Bluetooth connections to convert a Bluetooth header to
     * our system standard Network Header.  The base implementation just copies
     * the message ID and data length over.
     * @param bluetoothHeader the header to convert
     * @return A NetworkHeader representation of the BluetoothHeader
     */
    public NetworkHeader getNetworkHeader(BluetoothHeader bluetoothHeader) {
        NetworkHeader retVal = new NetworkHeader();
        retVal.SetMessageID(bluetoothHeader.GetMessageID());
        retVal.SetDataLength(bluetoothHeader.GetDataLength());
        retVal.SetTime(new Date().getTime() - m_BaseTime);

        // TODO: Use reflection to copy all like named fields

        return retVal;
    }

    /**
     * Called by Bluetooth connections to convert a NetworkHeader to
     * a Bluetooth Header.  The base implementation just copies
     * the message ID and data length over.
     * @param networkHeader the header to convert
     * @return A BluetoothHeader representation of the NetworkHeader
     */
    public BluetoothHeader getBluetoothHeader(NetworkHeader networkHeader) {
        BluetoothHeader retVal = new BluetoothHeader();
        retVal.SetMessageID(networkHeader.GetMessageID());

        // No match?  No send...
        if (retVal.GetMessageID() != networkHeader.GetMessageID() )
            retVal = null;

        // java is being difficult about type casts!
        int len = (int)networkHeader.GetDataLength();
        if (len < Short.MAX_VALUE)
        {
            // I *have* to cast to the smallest type that any Bluetooth Header might
            // use, or I get a compile error.  There's no way to cast to the type that
            // BluetoothHeader.GetDataLength returns!
            // This means we have a hard-coded limit of always using Short, to allow
            // anyone to use Short.  If anyone ever uses Char, this won't be sufficient, but
            // it'll be problematic to always cast to Char, because that limits size to 255 bytes!
            retVal.SetDataLength((short)len);
        }
        else
        {
            retVal = null;
        }

        // TODO: Use reflection to copy all like named fields

        return retVal;
    }

    /**
     * Called when a connection receives a message
     * @param srcConnection The connection the message came in on
     * @param header The NetworkHeader for this message
     * @param hdrBuf The ByteBuffer for the NetworkHeader
     * @param payloadBuf The payload buffer for the message
     * @return true if this method handled the message and it should be dropped
     */
    public boolean onMessage(IConnection srcConnection, NetworkHeader header, ByteBuffer hdrBuf,
                             ByteBuffer payloadBuf)
    {
        if (header.GetMessageID() == BandwidthTest.MSG_ID) {
            BandwidthTest msg = new BandwidthTest(hdrBuf, payloadBuf);
            for (int i = 0; i < BandwidthTest.TestDataFieldInfo.count; i++) {
                if (msg.GetTestData(i) == 0) {
                    msg.SetTestData((int) (new Date().getTime() - m_BaseTime), i);
                    break;
                }
            }
        }

        return false;
    }

    /**
     * Called when a connection receives a message
     * @param srcConnection The connection the message came in on
     * @param header The NetworkHeader for this message
     * @param hdrBug The ByteBuffer for the NetworkHeader
     * @param payloadBuf The payload buffer for the message
     * @return true if this method handled the message and it should be dropped
     */
    public boolean onMessage(IConnection srcConnection, BluetoothHeader header, ByteBuffer hdrBug,
                             ByteBuffer payloadBuf)
    {
        boolean retVal = false;

        return retVal;
    }
}