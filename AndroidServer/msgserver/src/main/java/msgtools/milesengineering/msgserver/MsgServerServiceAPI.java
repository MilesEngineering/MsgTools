package msgtools.milesengineering.msgserver;

import android.os.IBinder;
import android.os.Message;
import android.os.Messenger;
import android.os.RemoteException;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * This is a service client connection implementation that can be used by your Application
 * to communicate with the MsgServerService.  It's been packaged with the service
 * so it can be re-cycled by other applications and we have all message stuff in one place.
 */

public class MsgServerServiceAPI {
    private Messenger m_Service;

    /**
     * Message IDs for each API
     */
    public final static int ID_REQUEST_SERVERS = 1;
    public final static int ID_REQUEST_CONNECTIONS = 2;
    public final static int ID_REQUEST_START_LOGGING = 3;
    public final static int ID_REQUEST_STOP_LOGGING = 4;

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
        return sendMessage(messageId, null);
    }

    /**
     * Send with a JSON payload
     * @param messageId Message ID to send with
     * @param json Optional JSON payload (may be null)
     * @return true if sent, false if not
     */
    private boolean sendMessage(int messageId, String json) {
        boolean retVal = false;

        Message msg = Message.obtain(null, messageId, 0, 0, json);
        try {
            m_Service.send(msg);
            retVal = true;
        } catch (RemoteException e) {
            e.printStackTrace();
        }

        return retVal;
    }

    /**
     * Invoke to request that the MsgServerService respond with an intent
     * that provides a list of active servers.
     */
    public void requestServers() {
        sendMessage(ID_REQUEST_SERVERS);
    }

    /**
     * Invoke to request that the MsgServerService respond with an intent
     * that provides a list of active connections.
     */
    public void requestConnections() { sendMessage(ID_REQUEST_CONNECTIONS); }

    public void stopLogging() { sendMessage(ID_REQUEST_STOP_LOGGING); }

    public void startLogging(String filename, String msgVersion) {
        try {
            JSONObject jsonObj = new JSONObject();
            jsonObj.put("filename", filename);
            jsonObj.put("msgVersion", msgVersion);
            sendMessage(ID_REQUEST_START_LOGGING, jsonObj.toString());
        }
        catch(JSONException je) {
            je.printStackTrace();
        }
    }
}
