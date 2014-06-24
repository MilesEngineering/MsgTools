#ifndef REFLECTION_H
#define REFLECTION_H

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

            }
            else
            {
                r._msgById[msgInfo->ID()] = msgInfo;
            }
            if(r._msgByName.contains(msgInfo->Name()))
            {

            }
            else
            {
                r._msgByName[msgInfo->Name()] = msgInfo;
            }
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
