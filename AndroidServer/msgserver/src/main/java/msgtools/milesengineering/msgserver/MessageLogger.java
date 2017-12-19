package msgtools.milesengineering.msgserver;

import android.os.Environment;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Calendar;
import java.util.TimeZone;

import Network.StartLog;

/**
 * This class logs messages in binary format to a file on the expanded/public storage space
 * The log comprises a series of log messages, the first of which is a message version
 * message with some kind of user provided identifier for the version of messages
 * we're using.
 *
 * Performance Note: This class does all logging on the caller's thread right now.  We may find
 * that this holds things up too much and spin up a new thread to process the messages.
 * We're starting simple and we'll see where this goes...
 */
class MessageLogger {
    private static final String TAG = MessageLogger.class.getSimpleName();

    private String m_LogPath = null;
    private boolean m_IsEnabled = false;
    private String m_Filename = null;
    private String m_MsgVersion = null;
    private OutputStream m_LogWriter;

    /**
     * ctor - creates a directory at the root of storage using the given name
     *
     * @param baseDirectory name of the base directory
     */
    public MessageLogger(String baseDirectory) {
        // Create the base directory if we don't have it already
        File logDir = new File(Environment.getExternalStorageDirectory().getAbsolutePath(), baseDirectory);
        m_LogPath = logDir.getPath();
        if (logDir.exists() == false)
            if (logDir.mkdirs() == false)
                android.util.Log.e(TAG, "Unable to create storage folder!");
    }

    /**
     * Check to see if logging is enabled
     * @return true if enabled
     */
    public boolean isEnabled() {
        return m_IsEnabled;
    }

    /**
     * Get the filename we're currently logging to
     * @return Filename or null if logging isn't enabled
     */
    public String getFilename() {
        return m_IsEnabled == true ? m_Filename : null;
    }

    /**
     * Get the current msgVersion we've dumped to the log
     * @return Message version or null if logging isn't enabled
     */
    public String getMsgVersion() {
        return m_IsEnabled == true ? m_MsgVersion : null;
    }

    /**
     * Start logging into the indicated filename.  The file will be written in our base directory
     * and will have a header with a timestamp and the message version.  If you start logging on
     * a file that already exists it will be overwritten.
     *
     * @param filename Filename to log to
     * @param msgVersion Message version to put in the log "header"
     * @return null if successful, else an error message
     */
    public String startLogging(String filename, String msgVersion) {
        android.util.Log.d(TAG, "startLogging()");
        String retVal = null;

        if (m_IsEnabled == false ) {
            File logFile = new File( m_LogPath, filename );
            try {
                if ( logFile.exists() == false )
                    logFile.createNewFile();

                m_LogWriter = new BufferedOutputStream(new FileOutputStream( logFile ));
                m_Filename = filename;
                m_MsgVersion = msgVersion;
                m_IsEnabled = true;

                retVal = writeHeader();
            } catch (IOException e) {
                retVal = e.getMessage();
            }
        }
        else
            retVal = "Logging already started!";

        return retVal;
    }

    /**
     * Stop logging.  Does nothing if we aren't logging
     * @return an error message if we aren't logging
     */
    public String stopLogging() {
        android.util.Log.d(TAG, "stopLogging()");
        String retVal = null;

        if ( m_IsEnabled == true ) {
            try {
                m_LogWriter.flush();
                m_LogWriter.close();
            }
            catch(IOException ioe) {
                retVal = ioe.getMessage();
            }

            m_LogWriter = null;
            m_Filename = null;
            m_MsgVersion = null;
            m_IsEnabled = false;
        }
        else
            retVal = "Logging not enabled!";

        return retVal;
    }

    public void log(ByteBuffer header, ByteBuffer payload) {
        android.util.Log.d(TAG, "log()");

        if(m_IsEnabled == false)
            return;

        try {
            m_LogWriter.write(header.array());

            if (payload != null )
                m_LogWriter.write(payload.array());
        }
        catch(IOException ioe) {
            ioe.printStackTrace();
        }
    }

    private String writeHeader() {
        android.util.Log.d(TAG, "writeHeader()");

        // TODO: MessageLumberJack is expecting an optional sequence header.  We're not writing
        // that out right now, but if you want to add it, it would go here.

        // TODO: Need to write a header with message version info - I suggest we just add a
        // field to startLog and log the entire startLog message.  Commented out
        // code below for that
        String retVal = null;

//        StartLog startLog = new StartLog();
//        startLog.SetLogFileType((short)StartLog.LogFileTypes.Binary.intValue());
//
//        int i = 0;
//        for( char c : m_Filename.toCharArray() )
//            startLog.SetLogFileName((short) c, i++);
//
//        i = 0;
//        for( char c : m_MsgVersion.toCharArray() )
//            startLog.SetMessageVersion((short) c, i++);
//
//        try {
//            m_LogWriter.write(startLog.GetBuffer().array());
//        }
//        catch(IOException ioe) {
//            retVal = ioe.getMessage();
//        }

        return retVal;
    }
}
