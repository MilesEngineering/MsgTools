#ifndef __FIELD_ACCESS_H__
#define __FIELD_ACCESS_H__

#define Get_int8_t(location) FieldAccess::GetField<int8_t>(location)
#define Get_int16_t(location) FieldAccess::GetField<int16_t>(location)
#define Get_int32_t(location) FieldAccess::GetField<int32_t>(location)
#define Get_int64_t(location) FieldAccess::GetField<int64_t>(location)
#define Get_uint8_t(location) FieldAccess::GetField<uint8_t>(location)
#define Get_uint16_t(location) FieldAccess::GetField<uint16_t>(location)
#define Get_uint32_t(location) FieldAccess::GetField<uint32_t>(location)
#define Get_uint64_t(location) FieldAccess::GetField<uint64_t>(location)
#define Get_float(location) FieldAccess::GetField<float>(location)
#define Get_double(location) FieldAccess::GetField<float>(location)

#define Set_int8_t(location, value) FieldAccess::SetField<int8_t>(location, value)
#define Set_int16_t(location, value) FieldAccess::SetField<int16_t>(location, value)
#define Set_int32_t(location, value) FieldAccess::SetField<int32_t>(location, value)
#define Set_int64_t(location, value) FieldAccess::SetField<int64_t>(location, value)
#define Set_uint8_t(location, value) FieldAccess::SetField<uint8_t>(location, value)
#define Set_uint16_t(location, value) FieldAccess::SetField<uint16_t>(location, value)
#define Set_uint32_t(location, value) FieldAccess::SetField<uint32_t>(location, value)
#define Set_uint64_t(location, value) FieldAccess::SetField<uint64_t>(location, value)
#define Set_float(location, value) FieldAccess::SetField<float>(location, value)
#define Set_double(location, value) FieldAccess::SetField<float>(location, value)

/** \todo Do we need to support non-aligned fields?  If so, then the big endian version of the code below needs to do a copy a byte at a time */
/** \todo If we *don't* do non-aligned fields, then we can possible implement faster code for 16/32/64 bit types by using GCC's __builtin_bswap16,
    __builtin_bswap32, __builtin_bswap64, so we'd want template specializations for that. */
/** \todo Not sure if gcc will unroll the loops, but if it doesn't, we may want to do that manually. */
class FieldAccess
{
    public:
        template <typename AccessType>
        static inline void SetField(void* location, const AccessType& value)
        {
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
            *(AccessType*)location = value;
#else
            // copy bytes of value into location in swapped order
            uint8_t* dest = (uint8_t*)location;
            uint8_t* source = (uint8_t*)&value;

            for (int k = 0; k < sizeof(AccessType); k++)
                dest[k] = source[sizeof(AccessType) - k - 1];
#endif
        }
        template <typename AccessType>
        static inline AccessType GetField(void* location)
        {
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
            return *(AccessType*)location;
#else
            // copy bytes at location into aligned union, return value
            union
            {
                AccessType u;
                unsigned char u8[sizeof(AccessType)];
            } dest;
            uint8_t* source = (uint8_t*)location;

            for (int k = 0; k < sizeof(AccessType); k++)
                dest.u8[k] = source[sizeof(AccessType) - k - 1];
            return dest.u;
#endif
        }
};

#endif
