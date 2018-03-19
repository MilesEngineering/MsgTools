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
        int   Size() const { return _size; }

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

#endif
