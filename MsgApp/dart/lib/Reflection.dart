import 'package:msgtools/FieldInfo.dart';
import 'package:msgtools/MsgInfo.dart';

class Reflection
{
    factory Reflection() => _r;
    Reflection._internal();
    static final Reflection _r = new Reflection._internal();

    static MsgInfo FindMsgByName(String name) => _r._msgByName[name];
    static MsgInfo FindMsgByID(int id) => _r._msgById[id];
    static void AddMsg(MsgInfo msgInfo)
    {
        if(_r._msgById.containsKey(msgInfo.id))
        {
            //# Error, conflict in message ID!
        }
        else
        {
            _r._msgById[msgInfo.id] = msgInfo;
        }
        if(_r._msgByName.containsKey(msgInfo.name))
        {
            //# Error, conflict in message name!
        }
        else
        {
            _r._msgByName[msgInfo.name] = msgInfo;
        }
    }
    static String ToCSV(Message msg, {bool justHeader=false})
    {
        final StringBuffer ret = new StringBuffer();
        final MsgInfo msgInfo = FindMsgByID(msg.GetMessageID());
        if(msgInfo != null)
        {
            ret.write(msgInfo.name);
            for(String fieldName in msgInfo.fields.keys)
            {
                final FieldInfo fieldInfo = msgInfo.fields[fieldName];
                ret.write(', ');
                if(fieldInfo.count == 1)
                {
                    if(justHeader)
                        ret.write(fieldInfo.name);
                    else
                        ret.write(fieldInfo.Value(msg.GetDataPtr()));
                }
                else
                {
                    for(int i=0; i<fieldInfo.count; i++)
                    {
                        if(i != 0)
                            ret.write(', ');
                        if(justHeader)
                            ret.write('${fieldInfo.name}_${i.toString()}');
                        else
                            ret.write(fieldInfo.Value(msg.GetDataPtr(), i));
                    }
                }
            }
        }
        return ret.toString();
    }
    static Message FromCSV(String csv)
    {
        final List<String> params = csv.split(',');
        final MsgInfo msgInfo = FindMsgByName(params[0]);
        final Message msg = new Message(msgInfo.size);
        msg.SetMessageID(msgInfo.id);
        int paramIndex = 1;
        for(String fieldName in msgInfo.fields.keys)
        {
            final FieldInfo fieldInfo = msgInfo.fields[fieldName];
            for(int arrayElem=0; arrayElem<fieldInfo.count; arrayElem++)
            {
                if(paramIndex < params.length)
                {
                    msgInfo.fields[fieldName].SetValue(params[paramIndex], msg.GetDataPtr());
                    paramIndex++;
                }
                else
                {
                    return null;
                }
            }
        }
        return msg;
    }

    static String ToJSON(Message msg)
    {
        final StringBuffer ret = new StringBuffer();
        final MsgInfo msgInfo = FindMsgByID(msg.GetMessageID());
        if(msgInfo != null)
        {
            ret.write('${msgInfo.name} : {');
            bool firstTime = true;
            for(String fieldName in msgInfo.fields.keys)
            {
                final FieldInfo fieldInfo = msgInfo.fields[fieldName];
                if(!firstTime)
                    ret.write(', ');
                if(fieldInfo.count == 1)
                {
                    ret.write('${fieldInfo.name}: {${fieldInfo.Value(msg.data)}}');
                }
                else
                {
                    ret.write('${fieldInfo.name} : {');
                    for(int i=0; i<fieldInfo.count; i++)
                    {
                        if(i != 0)
                            ret.write(', ');
                        ret.write(fieldInfo.Value(msg.GetDataPtr()));
                    }
                    ret.write('}');
                }
                firstTime = false;
            }
            ret.write('}');
        }
        return ret.toString();
    }
    static Message FromJSON(String json) => null;

    Map<int, MsgInfo> _msgById;
    Map<String, MsgInfo> _msgByName;
}
