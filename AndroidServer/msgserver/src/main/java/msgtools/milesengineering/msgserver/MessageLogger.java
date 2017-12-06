package msgtools.milesengineering.msgserver;

import android.os.Environment;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Calendar;
import java.util.TimeZone;

/**
 * This class logs messages in JSON format to a file on the expanded/public storage space
 * The log comprises a series of JSON strings (one per "line"). The first
 * String in the file is ALWAYS a log header that includes the start time (in UTC),
 * and a free form msg version (so you can post process later).
 *
 * Each log entry after is a message - each message includes: Timestamp (at the time of log) in UTC,
 * id, header bytes, and payload bytes.
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
    private FileWriter m_LogWriter;

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

                m_LogWriter = new FileWriter( logFile );
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

    public void log(int id, ByteBuffer header, ByteBuffer payload) {
        android.util.Log.d(TAG, "log()");

        if(m_IsEnabled == false)
            return;

        JSONObject logEntry = new JSONObject();
        String timestamp = getTimestampStr();

        try {
            logEntry.put("log_ts", timestamp);
            JSONArray bytes = new JSONArray(header.array());
            logEntry.put("network_header", bytes);
            bytes = new JSONArray(payload.array());
            logEntry.put("payload", bytes);
        }
        catch( JSONException je ) {
            je.printStackTrace();
        }

        try {
            m_LogWriter.write(logEntry.toString());
            m_LogWriter.write('\n');
        }
        catch(IOException ioe) {
            ioe.printStackTrace();
        }
    }

    private String writeHeader() {
        android.util.Log.d(TAG, "writeHeader()");

        String retVal = null;

        // Assume the class properties are setup...
        JSONObject wrapper = new JSONObject();
        JSONObject header = new JSONObject();

        try {
            String timeStr = getTimestampStr();

            header.put("startTime", timeStr);
            header.put("msgVersion", m_MsgVersion);

            wrapper.put("log_metadata", header);
        }
        catch( JSONException je ) {
            je.printStackTrace();
        }

        try {
            m_LogWriter.write(wrapper.toString());
            m_LogWriter.write('\n');
        }
        catch(IOException ioe) {
            retVal = ioe.getMessage();
        }

        return retVal;
    }

    private String getTimestampStr() {
        return String.format("%tFT%<tTZ",
                        Calendar.getInstance(TimeZone.getTimeZone("Z")));
    }
}
