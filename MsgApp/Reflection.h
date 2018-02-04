#ifndef REFLECTION_H
#define REFLECTION_H

#include <QSharedPointer>

class Reflection
{
    public:
        static MsgInfo* FindMsgByName(QString name) { return Instance()._msgByName.value(name); }
        static MsgInfo* FindMsgByID(MsgInfo::MsgId id) { return Instance()._msgById.value(id); }
        static void AddMsg(MsgInfo* msgInfo)
        {
            Reflection& r = Instance();
            if(r._msgById.contains(msgInfo->ID()))
            {
                //# Error, conflict in message ID!
            }
            else
            {
                r._msgById[msgInfo->ID()] = msgInfo;
            }
            if(r._msgByName.contains(msgInfo->Name()))
            {
                //# Error, conflict in message name!
            }
            else
            {
                r._msgByName[msgInfo->Name()] = msgInfo;
            }
        }
        static QString ToCSV(Message* msg, bool justHeader=false)
        {
            QString ret = "";
            MsgInfo* msgInfo = Reflection::FindMsgByID(msg->GetMessageID());
            if(msgInfo)
            {
                // take a guess at preallocating, as an optimization.
                //ret.reserve(8+msgInfo->GetFields().count()*5);
                ret += msgInfo->Name();
                for(int fieldIndex=0; fieldIndex<msgInfo->GetFields().count();  fieldIndex++)
                {
                    FieldInfo* fieldInfo = msgInfo->GetFields()[fieldIndex];
                    ret += ", ";
                    if(fieldInfo->Count() == 1)
                    {
                        if(justHeader)
                            ret += fieldInfo->Name();
                        else
                            ret += fieldInfo->Value(msg->GetDataPtr());
                    }
                    else
                    {
                        for(int i=0; i<fieldInfo->Count(); i++)
                        {
                            if(i != 0)
                                ret += ", ";
                            if(justHeader)
                                ret += fieldInfo->Name() + "_" + QString("%1").arg(i);
                            else
                                ret += fieldInfo->Value(msg->GetDataPtr(), i);
                        }
                    }
                }
            }
            return ret;
        }
        static QSharedPointer<Message> FromCSV(QString csv)
        {
            QStringList params = csv.split(",");
            MsgInfo* msgInfo = Reflection::FindMsgByName(params[0]);
            QSharedPointer<Message> msg = QSharedPointer<Message>(new Message(msgInfo->Size()));
            msg->SetMessageID(msgInfo->ID());
            int paramIndex = 1;
            for(int fieldIndex=0; fieldIndex < msgInfo->GetFields().count(); fieldIndex++)
            {
                FieldInfo* fieldInfo = msgInfo->GetFields()[fieldIndex];
                for(int arrayElem=0; arrayElem<fieldInfo->Count(); arrayElem++)
                {
                    if(paramIndex < params.count())
                    {
                        msgInfo->GetFields()[fieldIndex]->SetValue(params[paramIndex], msg->GetDataPtr());
                        paramIndex++;
                    }
                    else
                    {
                        return QSharedPointer<Message>();
                    }
                }
            }
            return msg;
        }

        static QString ToJSON(Message* msg)
        {
            QString ret = "";
            MsgInfo* msgInfo = Reflection::FindMsgByID(msg->GetMessageID());
            if(msgInfo)
            {
                ret += msgInfo->Name() + ": {";
                for(int fieldIndex=0; fieldIndex<msgInfo->GetFields().count();  fieldIndex++)
                {
                    FieldInfo* fieldInfo = msgInfo->GetFields()[fieldIndex];
                    if(fieldIndex != 0)
                        ret += ", ";
                    if(fieldInfo->Count() == 1)
                    {
                        ret += QString("%1: {%2}").arg(fieldInfo->Name()).arg(fieldInfo->Value(msg->GetDataPtr()));
                    }
                    else
                    {
                        ret += fieldInfo->Name() + " : {";
                        for(int i=0; i<fieldInfo->Count(); i++)
                        {
                            if(i != 0)
                                ret += ", ";
                            ret += fieldInfo->Value(msg->GetDataPtr());
                        }
                        ret += "}";
                    }
                }
                ret += "}";
            }
            return ret;
        }
        static Message* FromJSON(QString /*json*/)
        {
            return NULL;
        }

    private:
        static Reflection& Instance()
        {
            static Reflection instance;
            return instance;
        }
        Reflection()
        : _msgById(),
          _msgByName()
        {
        }

        QHash<MsgInfo::MsgId, MsgInfo*> _msgById;
        QHash<QString, MsgInfo*> _msgByName;
};

#endif // REFLECTION_H
