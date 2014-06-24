#ifndef FIELD_INFO_H
#define FIELD_INFO_H

#include <QHash>

class FieldInfo
{
    public:
        FieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : _name(name), _description(desc), _units(units), _location(location), _fieldSize(size), _count(count)
        {
        }
        const QString Name() const { return _name; }
        const QString Description() const { return _description; }
        const QString Units() const { return _units; }
        int Count() const { return _count; }
        virtual void SetValue(QString value, Message& msg, int index = 0) const = 0;
        virtual const QString Value(Message& msg, int index = 0) const = 0;
    protected:
        QString _name;
        QString _description;
        QString _units;
        int     _location;
        int     _fieldSize;
        int     _count;
        
};

class IntFieldInfo : public  FieldInfo
{
    public:
        IntFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
};

class UIntFieldInfo : public  FieldInfo
{
    public:
        UIntFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : FieldInfo(name, desc, units, location, size, count)
        {
        }
        virtual void SetValue(QString value, Message& msg, int index = 0) const { msg.m_data[_location + index * _fieldSize] = value.toInt(); }
        virtual const QString Value(Message& msg, int index = 0) const
        {
            if(_units.toUpper() == "ASCII" && _count > 1)
            {
                QString ret = "";
                for(int i=0; i<_count; i++)
                {
                    if(msg.m_data[_location + i * _fieldSize] == 0)
                        break;
                    ret += msg.m_data[_location + i * _fieldSize];
                }
                return ret;
            }
            else
            {
                return QString("%1").arg(msg.m_data[_location + index * _fieldSize]);
            }
        }
};

class FloatFieldInfo : public  FieldInfo
{
    public:
        FloatFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
};

class EnumFieldInfo : public UIntFieldInfo
{
    public:
        EnumFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;
    private:
        QHash<uint64_t, QString> m_valToName;
        QHash<QString, uint64_t> m_nameToVal;
};

class BitfieldInfo : public UIntFieldInfo
{
    public:
        BitfieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, int startBit, int numBits);
        int NumBits() const;
    protected:
        virtual void FromUint64_t(uint64_t value, Message& msg, int index) const;
        virtual uint64_t ToUint64_t(Message& msg, int index) const;
    private:
        int      m_numBits;
        int      m_shift;
        uint64_t m_mask;
};

class ScaledFieldInfo : public UIntFieldInfo
{
    public:
        ScaledFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, double scale, double offset);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;

    private:
        double m_scale;
        double m_offset;
};

class ScaledBitfieldInfo : public  BitfieldInfo
{
    public:
        ScaledBitfieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, double scale, double offset, int startBit, int numBits);
        virtual void SetValue(QString value, Message& msg, int index = 0) const;
        virtual const QString Value(Message& msg, int index = 0) const;

    private:
        double m_scale;
        double m_offset;
};

#endif
