package msgplugin;

import headers.BluetoothHeader;
import headers.NetworkHeader;
import java.util.Date;

public class MessageHandler {
    public MessageHandler(long baseTime) {
        m_BaseTime = baseTime;
    }
    public long m_BaseTime;

    public NetworkHeader getNetworkHeader(BluetoothHeader bluetoothHeader) {
        NetworkHeader retVal = new NetworkHeader();
        retVal.SetMessageID(bluetoothHeader.GetMessageID());
        retVal.SetDataLength(bluetoothHeader.GetDataLength());
        retVal.SetTime(new Date().getTime() - m_BaseTime);

        // TODO: Use reflection to copy all like named fields

        return retVal;
    }

    public BluetoothHeader getBluetoothHeader(NetworkHeader networkHeader) {
        BluetoothHeader retVal = new BluetoothHeader();
        retVal.SetMessageID(networkHeader.GetMessageID());

        // No match?  No send...
        if (retVal.GetMessageID() != networkHeader.GetMessageID() )
            retVal = null;

        // java is being difficult about type casts!
        int len = networkHeader.GetDataLength();
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
}