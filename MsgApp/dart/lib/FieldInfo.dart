import 'dart:typed_data';

abstract class FieldInfo
{
    const FieldInfo(this.name, this.description, this.units, this.location, this.fieldSize, this.count);
    void SetValue(String value, ByteData data, [int index = 0]);
    String Value(ByteData data, [int index = 0]);

    final String  name;
    final String  description;
    final String  units;
    final int     location;
    final int     fieldSize;
    final int     count;
}


class IntFieldInfo extends FieldInfo
{
    const IntFieldInfo(String name, String desc, String units, int location, int size, int count)
    : super(name, desc, units, location, size, count);
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        FromInt64_t(int.parse(value), data, index);
    }
    @override String Value(ByteData data, [int index = 0])
    {
        if(units.toUpperCase() == 'ASCII' && count > 1)
        {
            final StringBuffer ret = new StringBuffer();
            for(int i=0; i<count; i++)
            {
                final String nextChar = new String.fromCharCode(ToInt64_t(data, i));
                if(nextChar == '\\0')
                    break;
                ret.write(nextChar);
            }
            return ret.toString();
        }
        else
        {
            return ToInt64_t(data, index).toString();
        }
    }
    void FromInt64_t(int value, ByteData data, int index)
    {
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 1: data.setInt8(loc, value);  break;
            case 2: data.setInt16(loc, value); break;
            case 4: data.setInt32(loc, value); break;
            case 8: data.setInt64(loc, value); break;
        }
    }
    int ToInt64_t(ByteData data, int index)
    {
        int value = 0;
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 1: value = data.getInt8(loc);  break;
            case 2: value = data.getInt16(loc); break;
            case 4: value = data.getInt32(loc); break;
            case 8: value = data.getInt64(loc); break;
        }
        return value;
    }
}

class UIntFieldInfo extends FieldInfo
{
    const UIntFieldInfo(String name, String desc, String units, int location, int size, int count)
    : super(name, desc, units, location, size, count);
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        FromUint64_t(int.parse(value), data, index);
    }
    @override String Value(ByteData data, [int index = 0])
    {
        if(units.toUpperCase() == 'ASCII' && count > 1)
        {
            final StringBuffer ret = new StringBuffer();
            for(int i=0; i<count; i++)
            {
                final String nextChar = new String.fromCharCode(ToUint64_t(data, i));
                if(nextChar == '\\0')
                    break;
                ret.write(nextChar);
            }
            return ret.toString();
        }
        else
        {
            return ToUint64_t(data, index).toString();
        }
    }
    void FromUint64_t(int value, ByteData data, int index)
    {
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 1: data.setUint8(loc, value);  break;
            case 2: data.setUint16(loc, value); break;
            case 4: data.setUint32(loc, value); break;
            case 8: data.setUint64(loc, value); break;
        }
    }
    int ToUint64_t(ByteData data, int index)
    {
        int value = 0;
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 1: value = data.getUint8(loc);  break;
            case 2: value = data.getUint16(loc); break;
            case 4: value = data.getUint32(loc); break;
            case 8: value = data.getUint64(loc); break;
        }
        return value;
    }
}

class FloatFieldInfo extends FieldInfo
{
    const FloatFieldInfo(String name, String desc, String units, int location, int size, int count)
    : super(name, desc, units, location, size, count);
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 4: data.setFloat32(loc, double.parse(value));  break;
            case 8: data.setFloat64(loc, double.parse(value)); break;
        }
    }
    @override String Value(ByteData data, [int index = 0])
    {
        String value = '';
        final int loc = location + index * fieldSize;
        switch(fieldSize)
        {
            case 4: value = data.getFloat32(loc).toString(); break;
            case 8: value = data.getFloat64(loc).toString(); break;
        }
        return value;
    }
}

class EnumFieldInfo extends UIntFieldInfo
{
    const EnumFieldInfo(String name, String desc, String units, int location, int size, int count, this._valToName, this._nameToVal)
    : super(name, desc, units, location, size, count);
    /*{
        \todo Need to populate hash tables to convert between int and enum string!
    }*/
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        String v = value;
        if(_nameToVal.containsKey(value))
            v = _nameToVal[value].toString();
        super.SetValue(v, data, index);
    }
    @override String Value(ByteData data, [int index = 0])
    {
        String ret = super.Value(data, index);
        final int intVal = int.parse(ret);
        if(_valToName.containsKey(intVal))
            ret = _valToName[intVal];
        return ret;
    }
    final Map<int, String> _valToName;
    final Map<String, int> _nameToVal;
}

class BitfieldInfo extends UIntFieldInfo
{
    const BitfieldInfo(String name, String desc, String units, int location, int size, int count, this._shift, int numBits)
    : _mask = ((1 << numBits) - 1) << _shift,
     super(name, desc, units, location, size, count);
    @override void FromUint64_t(int value, ByteData data, int index)
    {
        int parent = super.ToUint64_t(data, index);
        parent &= ~_mask;
        parent |= (value << _shift);
        super.FromUint64_t(parent, data, index);
    }
    @override int ToUint64_t(ByteData data, int index)
    {
        final int parent = super.ToUint64_t(data, index);
        return  (parent & _mask) >> _shift;
    }

    final int _shift;
    final int _mask;
}

class ScaledFieldInfo extends UIntFieldInfo
{
    const ScaledFieldInfo(String name, String desc, String units, int location, int size, int count, this._scale, this._offset)
    : super(name, desc, units, location, size, count);
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        super.FromUint64_t(((double.parse(value) - _offset) ~/ _scale), data, index);
    }
    @override String Value(ByteData data, [int index = 0])
    {
        final double value = super.ToUint64_t(data, index) * _scale + _offset;
        return value.toString();
    }

    final double _scale;
    final double _offset;
}

class ScaledBitfieldInfo extends BitfieldInfo
{
    const ScaledBitfieldInfo(String name, String desc, String units, int location, int size, int count, this._scale, this._offset, int startBit, int numBits)
    : super(name, desc, units, location, size, count, startBit, numBits);
    @override void SetValue(String value, ByteData data, [int index = 0])
    {
        super.FromUint64_t(((double.parse(value) - _offset) ~/ _scale), data, index);
    }
    @override String Value(ByteData data, [int index = 0])
    {
        final double value = super.ToUint64_t(data, index) * _scale + _offset;
        return value.toString();
    }

    final double _scale;
    final double _offset;
}
