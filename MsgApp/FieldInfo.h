#ifndef FIELD_INFO_H
#define FIELD_INFO_H

class FieldInfo
{
    public:
        FieldInfo(char* name, char* desc, char* units, int location, int size, int count);
        QString Name();
        QString Description();
        QString Units();
        int Count();
        virtual void SetValue(QString value, Message& msg, int index = 0) const = 0;
        virtual const QString Value(Message& msg, int index = 0) const = 0;
    private:
        QString _name;
        QString _description;
        QString _units;
        int     _fieldSize;
        int     _count;
        
};

class IntFieldInfo : public  FieldInfo
{
    public:
        IntFieldInfo(char* name, char* desc, char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
};

class UIntFieldInfo : public  FieldInfo
{
    public:
        UIntFieldInfo(char* name, char* desc, char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
};

class FloatFieldInfo : public  FieldInfo
{
    public:
        FloatFieldInfo(char* name, char* desc, char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
};

class EnumFieldInfo : public UIntInfo
{
    public:
        EnumFieldInfo(char* name, char* desc, char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
    private:
        QHash<uint64_t, QString> m_valToName;
        QHash<QString, uint64_t> m_nameToVal;
};

class BitfieldInfo : public UIntInfo
{
    public:
        BitfieldInfo(char* name, char* desc, char* units, int location, int size, int count, int startBit, int numBits);
        int NumBits() const;
    protected:
        virtual void FromUint64_t(uint64_t value, Message& msg, int index) const;
        virtual uint64_t ToUint64_t(Message& msg, int index) const;
    private:
        int      m_numBits;
        int      m_shift;
        uint64_t m_mask;
};

class ScaledFieldInfo : public UIntInfo
{
    public:
        ScaledFieldInfo(char* name, char* desc, char* units, int location, int size, int count, double scale, double offset);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;

    private:
        double m_scale;
        double m_offset;
};

class ScaledBitfieldInfo : public  BitfieldInfo
{
    public:
        ScaledBitfieldInfo(char* name, char* desc, char* units, int location, int size, int count, double scale, double offset, int startBit, int numBits);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;

    private:
        double m_scale;
        double m_offset;
};

#endif
