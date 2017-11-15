package msgtools.milesengineering.msgserver;

import android.os.IBinder;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;

/**
 * This is a service client connection implementation that can be used by your Application
 * to communicate with the MsgServerService.  It's been packaged with the service
 * so it can be re-cycled by other applications and we have all message stuff in one place.
 */

public class MsgServerServiceAPI {
    private Messenger m_Service;

    /**
     * New instance from a binder
     * @param service The IBinder interface returned from the service on bind request.
     */
    public MsgServerServiceAPI(IBinder service) {
        m_Service = new Messenger(service);
    }

    /**
     * Utilty method to send a message without params
     * @param messageId ID of the message to send
     * @return true if the message was sent, else false
     */
    private boolean sendMessage( int messageId ) {
        boolean retVal = false;

        Message msg = Message.obtain(null, messageId, 0, 0);
        try {
            m_Service.send(msg);
            retVal = true;
        } catch (RemoteException e) {
            e.printStackTrace();
        }

        return retVal;
    }

    public void test() {
        sendMessage( 0 );
    }
}
