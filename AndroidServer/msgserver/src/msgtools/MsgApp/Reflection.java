package MsgApp;

import java.lang.Class;
import java.lang.reflect.*;
import java.util.Hashtable;
import java.util.List;
import java.util.ArrayList;
import java.nio.ByteBuffer;

import headers.NetworkHeader;

public class Reflection
{
    public static Hashtable<Integer, MsgInfo> msgsById = new Hashtable<Integer, MsgInfo>();
    public static Hashtable<String, MsgInfo> msgsByName = new Hashtable<String, MsgInfo>();
    
    static Message Factory(ByteBuffer buff) throws NoSuchMethodException, InstantiationException, InvocationTargetException, IllegalAccessException
    {
        headers.NetworkHeader hdr = new headers.NetworkHeader(buff);
        MsgInfo info = msgsById.get(hdr.GetMessageID());
        Class<?> msgClass = info.msgClass;
        Constructor<?> constructor = msgClass.getConstructor(ByteBuffer.class);
        Message msg = (Message)constructor.newInstance(buff);
        return msg;
    }
};
