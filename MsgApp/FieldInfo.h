#ifndef FIELD_INFO_H
#define FIELD_INFO_H

#include <QString>
#include <QHash>
#include "FieldAccess.h"

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
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const = 0;
        virtual const QString Value(uint8_t* data, int index = 0) const = 0;
        int Size() const { return _fieldSize; }
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
        IntFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : FieldInfo(name, desc, units, location, size, count)
        {
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            FromInt64_t(value.toInt(), data, index);
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            if(_units.toUpper() == "ASCII" && _count > 1)
            {
                QString ret = "";
                for(int i=0; i<_count; i++)
                {
                    char value = ToInt64_t(data, i);
                    if(value == 0)
                        break;
                    ret += value;
                }
                return ret;
            }
            else
            {
                return QString("%1").arg(ToInt64_t(data, index));
            }
        }
        virtual void FromInt64_t(uint64_t value, uint8_t* data, int index) const
        {
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 1:
                    Set_int8_t(ptr, value);
                    break;
                case 2:
                    Set_int16_t(ptr, value);
                    break;
                case 4:
                    Set_int32_t(ptr, value);
                    break;
                case 8:
                    Set_int64_t(ptr, value);
                    break;
            }
        }
        virtual uint64_t ToInt64_t(uint8_t* data, int index) const
        {
            uint64_t value = 0;
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 1:
                    value = Get_int8_t(ptr);
                    break;
                case 2:
                    value = Get_int16_t(ptr);
                    break;
                case 4:
                    value = Get_int32_t(ptr);
                    break;
                case 8:
                    value = Get_int64_t(ptr);
                    break;
            }
            return value;
        }
};

class UIntFieldInfo : public  FieldInfo
{
    public:
        UIntFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : FieldInfo(name, desc, units, location, size, count)
        {
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            FromUint64_t(value.toInt(), data, index);
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            if(_units.toUpper() == "ASCII" && _count > 1)
            {
                QString ret = "";
                for(int i=0; i<_count; i++)
                {
                    char value = ToUint64_t(data, i);
                    if(value == 0)
                        break;
                    ret += value;
                }
                return ret;
            }
            else
            {
                return QString("%1").arg(ToUint64_t(data, index));
            }
        }
        virtual void FromUint64_t(uint64_t value, uint8_t* data, int index) const
        {
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 1:
                    Set_uint8_t(ptr, value);
                    break;
                case 2:
                    Set_uint16_t(ptr, value);
                    break;
                case 4:
                    Set_uint32_t(ptr, value);
                    break;
                case 8:
                    Set_uint64_t(ptr, value);
                    break;
            }
        }
        virtual uint64_t ToUint64_t(uint8_t* data, int index) const
        {
            uint64_t value = 0;
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 1:
                    value = Get_uint8_t(ptr);
                    break;
                case 2:
                    value = Get_uint16_t(ptr);
                    break;
                case 4:
                    value = Get_uint32_t(ptr);
                    break;
                case 8:
                    value = Get_uint64_t(ptr);
                    break;
            }
            return value;
        }
};

class FloatFieldInfo : public  FieldInfo
{
    public:
        FloatFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : FieldInfo(name, desc, units, location, size, count)
        {
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 4:
                    Set_float(ptr, value.toFloat());
                    break;
                case 8:
                    Set_double(ptr, value.toDouble());
                    break;
            }
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            QString value("");
            uint8_t* ptr = &data[_location + index * _fieldSize];
            switch(_fieldSize)
            {
                case 4:
                    value = QString("%1").arg(Get_float(ptr));
                    break;
                case 8:
                    value = QString("%1").arg(Get_double(ptr));
                    break;
            }
            return value;
        }
};

class EnumFieldInfo : public UIntFieldInfo
{
    public:
        EnumFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count)
        : UIntFieldInfo(name, desc, units, location, size, count)
        {
            /** \todo Need to populate hash tables to convert between int and enum string! */
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            if(_nameToVal.contains(value))
                value = QString("%1").arg(_nameToVal[value]);
            UIntFieldInfo::SetValue(value, data, index);
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            QString ret = UIntFieldInfo::Value(data, index);
            uint64_t intVal = ret.toInt();
            if(_valToName.contains(intVal))
                ret = _valToName[intVal];
            return ret;
        }
    private:
        QHash<uint64_t, QString> _valToName;
        QHash<QString, uint64_t> _nameToVal;
};

class BitfieldInfo : public UIntFieldInfo
{
    public:
        BitfieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, int startBit, int numBits)
        : UIntFieldInfo(name, desc, units, location, size, count),
          _numBits(numBits),
          _shift(startBit)
        {
            _mask = ((1 << _numBits) - 1) << _shift;
        }
        virtual void FromUint64_t(uint64_t value, uint8_t* data, int index) const
        {
            uint64_t parent = UIntFieldInfo::ToUint64_t(data, index);
            parent &= ~_mask;
            parent |= (value << _shift);
            UIntFieldInfo::FromUint64_t(parent, data, index);
        }
        virtual uint64_t ToUint64_t(uint8_t* data, int index) const
        {
            uint64_t parent = UIntFieldInfo::ToUint64_t(data, index);
            return  (parent & _mask) >> _shift;
        }
    private:
        int      _numBits;
        int      _shift;
        uint64_t _mask;
};

class ScaledFieldInfo : public UIntFieldInfo
{
    public:
        ScaledFieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, double scale, double offset)
        : UIntFieldInfo(name, desc, units, location, size, count),
          _scale(scale),
          _offset(offset)
        {
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            UIntFieldInfo::FromUint64_t((value.toDouble() - _offset) / _scale, data, index);
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            float value = UIntFieldInfo::ToUint64_t(data, index) * _scale + _offset;
            return QString("%1").arg(value);
        }
    private:
        double _scale;
        double _offset;
};

class ScaledBitfieldInfo : public  BitfieldInfo
{
    public:
        ScaledBitfieldInfo(const char* name, const char* desc, const char* units, int location, int size, int count, double scale, double offset, int startBit, int numBits)
        : BitfieldInfo(name, desc, units, location, size, count, startBit, numBits),
          _scale(scale),
          _offset(offset)
        {
        }
        virtual void SetValue(QString value, uint8_t* data, int index = 0) const
        {
            BitfieldInfo::FromUint64_t((value.toDouble() - _offset) / _scale, data, index);
        }
        virtual const QString Value(uint8_t* data, int index = 0) const
        {
            float value = BitfieldInfo::ToUint64_t(data, index) * _scale + _offset;
            return QString("%1").arg(value);
        }

    private:
        double _scale;
        double _offset;
};

#endif
