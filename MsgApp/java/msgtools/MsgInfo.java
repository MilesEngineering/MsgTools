package msgtools;

import java.util.Hashtable;
import java.util.List;
import java.util.ArrayList;
import java.nio.ByteBuffer;

public class MsgInfo
{
    public List<FieldInfo> fields;
    public int id;
    public String name;
    public String comment;
    public int size;
    public Class<?> msgClass;
    public MsgInfo(Class<?> cl, int i, String c, int s)
    {
        msgClass = cl;
        id = i;
        name = msgClass.getName();
        comment = c;
        size = s;

        fields = new ArrayList<FieldInfo>();
        Reflection.msgsById.put(id, this);
        Reflection.msgsByName.put(name, this);
    }
    public void AddField(FieldInfo f)
    {
        fields.add(f);
    }
};
