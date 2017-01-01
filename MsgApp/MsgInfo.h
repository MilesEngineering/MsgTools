#ifndef MSG_INFO_H
#define MSG_INFO_H

#include <QHash>
#include <QVector>
#include <stdint.h>

class MsgInfo
{
    public:
        typedef uint32_t MsgId;
        MsgInfo(MsgId id, QString name, QString description, int size)
        : _fields(),
          _fieldHash(),
          _id(id),
          _name(name),
          _description(description),
          _size(size)
        {
        }
        ~MsgInfo() {}

        const QString Name() const { return _name; }
        MsgId ID() const { return _id; }
        int   Size() const;

        const QVector<FieldInfo *>& GetFields() const { return _fields; }
        const FieldInfo*            GetField(QString name) const { return _fieldHash.value(name); }

        void AddField(FieldInfo* fieldInfo) { _fields.append(fieldInfo); _fieldHash[fieldInfo->Name()] = fieldInfo; }

    private:
        QVector<FieldInfo *>       _fields;
        QHash<QString, FieldInfo*> _fieldHash;
        MsgId                      _id;
        QString                    _name;
        QString                    _description;
        int                        _size;
};

/** Utility class to cache FieldInfo by QString, for a given msgInfo. */
class FieldInfoCache
{
public:
    FieldInfoCache()
    : fieldInfos()
    {
    }
    FieldInfo* lookup(MsgInfo* msgInfo, const QString& name)
    {
        if(!fieldInfos.contains(name))
        {
            FieldInfo* fi = 0;
            foreach(FieldInfo* fieldInfo, msgInfo->GetFields())
            {
                if(fieldInfo->Name().contains(name))
                {
                    fi = fieldInfo;
                    break;
                }
            }
            fieldInfos[name] = fi;
        }
        return fieldInfos[name];
    }
    private:
        QHash<QString, FieldInfo*> fieldInfos;
};

#endif
