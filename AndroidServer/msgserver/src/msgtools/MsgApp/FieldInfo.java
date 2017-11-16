package MsgApp;

public class FieldInfo
{
    public FieldInfo(String n, String d, String u, int c)
    {
        name = n;
        description = d;
        units = u;
        count = c;
    }
    public String get(Message message) throws  java.lang.reflect.InvocationTargetException, NoSuchMethodException, IllegalArgumentException, IllegalAccessException
    {
        // need class of message that matches the ID!
        Class<?> c = message.getClass();
        if(count == 1)
        {
            java.lang.reflect.Method method = c.getMethod("Get" + name);
            Object o = method.invoke(message);
            return String.valueOf(o);
        }
        else
        {
            java.lang.reflect.Method method = c.getMethod("Get" + name, int.class);
            String ret="";
            for(int i=0; i<count; i++)
            {
                Object o = method.invoke(message, i);
                ret += String.valueOf(o);
                if(i<count-1)
                    ret += ", ";
            }
            return ret;
        }
    }
    public void set(Message message, String value) throws  java.lang.reflect.InvocationTargetException, NoSuchMethodException, IllegalArgumentException, IllegalAccessException
    {
        Class<?> c = message.getClass();
        java.lang.reflect.Method method = c.getMethod("Set" + name);
        method.invoke(message, value);
    }
    public String name;
    public String description;
    public String units;
    public int count;
};
