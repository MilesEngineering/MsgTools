#ifndef __FIELD_ACCESS_H__
#define __FIELD_ACCESS_H__

#define INLINE inline
#ifndef UNUSED
#define UNUSED (void)
#endif

#define Get_int8_t(location) FieldAccess::GetField<int8_t>(location)
#define Get_int16_t(location) FieldAccess::GetField<int16_t>(location)
#define Get_int32_t(location) FieldAccess::GetField<int32_t>(location)
#define Get_int64_t(location) FieldAccess::GetField<int64_t>(location)
#define Get_uint8_t(location) FieldAccess::GetField<uint8_t>(location)
#define Get_uint16_t(location) FieldAccess::GetField<uint16_t>(location)
#define Get_uint32_t(location) FieldAccess::GetField<uint32_t>(location)
#define Get_uint64_t(location) FieldAccess::GetField<uint64_t>(location)
#define Get_float(location) FieldAccess::GetField<float>(location)
#define Get_double(location) FieldAccess::GetField<double>(location)

#define Set_int8_t(location, value) FieldAccess::SetField<int8_t>(location, value)
#define Set_int16_t(location, value) FieldAccess::SetField<int16_t>(location, value)
#define Set_int32_t(location, value) FieldAccess::SetField<int32_t>(location, value)
#define Set_int64_t(location, value) FieldAccess::SetField<int64_t>(location, value)
#define Set_uint8_t(location, value) FieldAccess::SetField<uint8_t>(location, value)
#define Set_uint16_t(location, value) FieldAccess::SetField<uint16_t>(location, value)
#define Set_uint32_t(location, value) FieldAccess::SetField<uint32_t>(location, value)
#define Set_uint64_t(location, value) FieldAccess::SetField<uint64_t>(location, value)
#define Set_float(location, value) FieldAccess::SetField<float>(location, value)
#define Set_double(location, value) FieldAccess::SetField<double>(location, value)

/** \todo If we change the S/Get_xxx() functions to take (msgLocation, offset), and we
    assume the msgLocation is aligned and that offset is a compile-time constant, if we're
    smart we can do a compile-time choice of aligned field (so, pointer dereference), vs.
    unaligned field (byte copy one at a time), for each field's accessor code. */
/** \todo For aligned fields, where we need to swap endian, we can possibly implement faster code
    for 16/32/64 bit types by using GCC's __builtin_bswap16,
    __builtin_bswap32, __builtin_bswap64, so we'd want template specializations for that. */
/** \todo Not sure if gcc will unroll the loops, but if it doesn't, we may want to do that manually. */
class FieldAccess
{
    public:
        template <typename AccessType>
        static inline void SetField(void* location, const AccessType& value)
        {
            // copy bytes of value into location in swapped order
            uint8_t* dest = (uint8_t*)location;
            uint8_t* source = (uint8_t*)&value;

            for (unsigned k = 0; k < sizeof(AccessType); k++)
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
                dest[k] = source[k];
#else
                dest[k] = source[sizeof(AccessType) - k - 1];
#endif
        }
        template <typename AccessType>
        static inline AccessType GetField(const void* location)
        {
            // copy bytes at location into aligned union, return value
            union
            {
                AccessType u;
                unsigned char u8[sizeof(AccessType)];
            } dest;
            const uint8_t* source = (const uint8_t*)location;

            for (unsigned k = 0; k < sizeof(AccessType); k++)
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
                dest.u8[k] = source[k];
#else
                dest.u8[k] = source[sizeof(AccessType) - k - 1];
#endif
            return dest.u;
        }
};

#endif
