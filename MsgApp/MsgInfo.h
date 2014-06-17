#ifndef MSG_INFO_H
#define MSG_INFO_H

class MsgInfo
{
    public:
        MsgInfo();
        ~MsgInfo() {}

        const QString Name() const;
        MsgId ID() const;
        int   Size() const;

        const QVector<MsgFieldInfo *>& GetFields() const;
        const MsgFieldInfo*            GetField(QString name) const;

    private:
        QVector<MsgFieldInfo *>    _fields;
        QHash<QString, FieldInfo*> _fieldHash;
        QString                    _name;
        QString                    _description;
        int                        _size;
};

#endif
