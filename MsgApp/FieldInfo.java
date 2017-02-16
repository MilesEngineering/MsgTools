package MsgApp;

public class FieldInfo
{
    public FieldInfo(String name, String description, String units, int count)
    {
        fieldName = name;
    }
    public String get(Message message) throws  java.lang.reflect.InvocationTargetException, NoSuchMethodException, IllegalArgumentException, IllegalAccessException
    {
        Class<?> c = message.getClass();
        java.lang.reflect.Method method = c.getMethod("Get" + fieldName);
        Object o = method.invoke(message);
        return String.valueOf(o);
    }
    public void set(Message message, String value) throws  java.lang.reflect.InvocationTargetException, NoSuchMethodException, IllegalArgumentException, IllegalAccessException
    {
        Class<?> c = message.getClass();
        java.lang.reflect.Method method = c.getMethod("Set" + fieldName);
        method.invoke(message, value);
    }
    String fieldName;
};
