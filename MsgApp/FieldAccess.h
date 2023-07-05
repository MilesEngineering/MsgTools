#ifndef __FIELD_ACCESS_H__
#define __FIELD_ACCESS_H__

#ifndef UNUSED
#define UNUSED (void)
#endif

#ifndef INLINE
#define INLINE
#endif

// Aligned native endian fields are accessed by dereferencing pointers.
class FieldAccessAlignedNativeEndian
{
    public:
        template <typename AccessType>
        static inline void SetField(void* location, const AccessType& value)
        {
            *(AccessType*)location = value;
        }
        template <typename AccessType>
        static inline AccessType GetField(const void* location)
        {
            return *(AccessType*)location;
        }
};

// Unaligned fields are accessed by copying them a byte at a time.
class FieldAccessLE
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

// Unaligned fields are accessed by copying them a byte at a time.
class FieldAccessBE
{
    public:
        template <typename AccessType>
        static inline void SetField(void* location, const AccessType& value)
        {
            // copy bytes of value into location in swapped order
            uint8_t* dest = (uint8_t*)location;
            uint8_t* source = (uint8_t*)&value;

            for (unsigned k = 0; k < sizeof(AccessType); k++)
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
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
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
                dest.u8[k] = source[k];
#else
                dest.u8[k] = source[sizeof(AccessType) - k - 1];
#endif
            return dest.u;
        }
};

// #defines to access little-endian unaligned fields.
#define GetLE_int8_t(location) FieldAccessLE::GetField<int8_t>(location)
#define GetLE_int16_t(location) FieldAccessLE::GetField<int16_t>(location)
#define GetLE_int32_t(location) FieldAccessLE::GetField<int32_t>(location)
#define GetLE_int64_t(location) FieldAccessLE::GetField<int64_t>(location)
#define GetLE_uint8_t(location) FieldAccessLE::GetField<uint8_t>(location)
#define GetLE_uint16_t(location) FieldAccessLE::GetField<uint16_t>(location)
#define GetLE_uint32_t(location) FieldAccessLE::GetField<uint32_t>(location)
#define GetLE_uint64_t(location) FieldAccessLE::GetField<uint64_t>(location)
#define GetLE_float(location) FieldAccessLE::GetField<float>(location)
#define GetLE_double(location) FieldAccessLE::GetField<double>(location)

#define SetLE_int8_t(location, value) FieldAccessLE::SetField<int8_t>(location, value)
#define SetLE_int16_t(location, value) FieldAccessLE::SetField<int16_t>(location, value)
#define SetLE_int32_t(location, value) FieldAccessLE::SetField<int32_t>(location, value)
#define SetLE_int64_t(location, value) FieldAccessLE::SetField<int64_t>(location, value)
#define SetLE_uint8_t(location, value) FieldAccessLE::SetField<uint8_t>(location, value)
#define SetLE_uint16_t(location, value) FieldAccessLE::SetField<uint16_t>(location, value)
#define SetLE_uint32_t(location, value) FieldAccessLE::SetField<uint32_t>(location, value)
#define SetLE_uint64_t(location, value) FieldAccessLE::SetField<uint64_t>(location, value)
#define SetLE_float(location, value) FieldAccessLE::SetField<float>(location, value)
#define SetLE_double(location, value) FieldAccessLE::SetField<double>(location, value)

// #defines to access big-endian unaligned fields.
#define GetBE_int8_t(location) FieldAccessBE::GetField<int8_t>(location)
#define GetBE_int16_t(location) FieldAccessBE::GetField<int16_t>(location)
#define GetBE_int32_t(location) FieldAccessBE::GetField<int32_t>(location)
#define GetBE_int64_t(location) FieldAccessBE::GetField<int64_t>(location)
#define GetBE_uint8_t(location) FieldAccessBE::GetField<uint8_t>(location)
#define GetBE_uint16_t(location) FieldAccessBE::GetField<uint16_t>(location)
#define GetBE_uint32_t(location) FieldAccessBE::GetField<uint32_t>(location)
#define GetBE_uint64_t(location) FieldAccessBE::GetField<uint64_t>(location)
#define GetBE_float(location) FieldAccessBE::GetField<float>(location)
#define GetBE_double(location) FieldAccessBE::GetField<double>(location)

#define SetBE_int8_t(location, value) FieldAccessBE::SetField<int8_t>(location, value)
#define SetBE_int16_t(location, value) FieldAccessBE::SetField<int16_t>(location, value)
#define SetBE_int32_t(location, value) FieldAccessBE::SetField<int32_t>(location, value)
#define SetBE_int64_t(location, value) FieldAccessBE::SetField<int64_t>(location, value)
#define SetBE_uint8_t(location, value) FieldAccessBE::SetField<uint8_t>(location, value)
#define SetBE_uint16_t(location, value) FieldAccessBE::SetField<uint16_t>(location, value)
#define SetBE_uint32_t(location, value) FieldAccessBE::SetField<uint32_t>(location, value)
#define SetBE_uint64_t(location, value) FieldAccessBE::SetField<uint64_t>(location, value)
#define SetBE_float(location, value) FieldAccessBE::SetField<float>(location, value)
#define SetBE_double(location, value) FieldAccessBE::SetField<double>(location, value)


#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    // #defines to access native endian aligned fields directly.
    #define GetAlignedLE_int8_t(location) FieldAccessAlignedNativeEndian::GetField<int8_t>(location)
    #define GetAlignedLE_int16_t(location) FieldAccessAlignedNativeEndian::GetField<int16_t>(location)
    #define GetAlignedLE_int32_t(location) FieldAccessAlignedNativeEndian::GetField<int32_t>(location)
    #define GetAlignedLE_int64_t(location) FieldAccessAlignedNativeEndian::GetField<int64_t>(location)
    #define GetAlignedLE_uint8_t(location) FieldAccessAlignedNativeEndian::GetField<uint8_t>(location)
    #define GetAlignedLE_uint16_t(location) FieldAccessAlignedNativeEndian::GetField<uint16_t>(location)
    #define GetAlignedLE_uint32_t(location) FieldAccessAlignedNativeEndian::GetField<uint32_t>(location)
    #define GetAlignedLE_uint64_t(location) FieldAccessAlignedNativeEndian::GetField<uint64_t>(location)
    #define GetAlignedLE_float(location) FieldAccessAlignedNativeEndian::GetField<float>(location)
    #define GetAlignedLE_double(location) FieldAccessAlignedNativeEndian::GetField<double>(location)

    #define SetAlignedLE_int8_t(location, value) FieldAccessAlignedNativeEndian::SetField<int8_t>(location, value)
    #define SetAlignedLE_int16_t(location, value) FieldAccessAlignedNativeEndian::SetField<int16_t>(location, value)
    #define SetAlignedLE_int32_t(location, value) FieldAccessAlignedNativeEndian::SetField<int32_t>(location, value)
    #define SetAlignedLE_int64_t(location, value) FieldAccessAlignedNativeEndian::SetField<int64_t>(location, value)
    #define SetAlignedLE_uint8_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint8_t>(location, value)
    #define SetAlignedLE_uint16_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint16_t>(location, value)
    #define SetAlignedLE_uint32_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint32_t>(location, value)
    #define SetAlignedLE_uint64_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint64_t>(location, value)
    #define SetAlignedLE_float(location, value) FieldAccessAlignedNativeEndian::SetField<float>(location, value)
    #define SetAlignedLE_double(location, value) FieldAccessAlignedNativeEndian::SetField<double>(location, value)
    
    // #defines to access non-native endian aligned fields, using the unaligned
    // access functions to copy them a byte at a time.
    #define GetAlignedBE_int8_t(location) FieldAccessBE::GetField<int8_t>(location)
    #define GetAlignedBE_int16_t(location) FieldAccessBE::GetField<int16_t>(location)
    #define GetAlignedBE_int32_t(location) FieldAccessBE::GetField<int32_t>(location)
    #define GetAlignedBE_int64_t(location) FieldAccessBE::GetField<int64_t>(location)
    #define GetAlignedBE_uint8_t(location) FieldAccessBE::GetField<uint8_t>(location)
    #define GetAlignedBE_uint16_t(location) FieldAccessBE::GetField<uint16_t>(location)
    #define GetAlignedBE_uint32_t(location) FieldAccessBE::GetField<uint32_t>(location)
    #define GetAlignedBE_uint64_t(location) FieldAccessBE::GetField<uint64_t>(location)
    #define GetAlignedBE_float(location) FieldAccessBE::GetField<float>(location)
    #define GetAlignedBE_double(location) FieldAccessBE::GetField<double>(location)

    #define SetAlignedBE_int8_t(location, value) FieldAccessBE::SetField<int8_t>(location, value)
    #define SetAlignedBE_int16_t(location, value) FieldAccessBE::SetField<int16_t>(location, value)
    #define SetAlignedBE_int32_t(location, value) FieldAccessBE::SetField<int32_t>(location, value)
    #define SetAlignedBE_int64_t(location, value) FieldAccessBE::SetField<int64_t>(location, value)
    #define SetAlignedBE_uint8_t(location, value) FieldAccessBE::SetField<uint8_t>(location, value)
    #define SetAlignedBE_uint16_t(location, value) FieldAccessBE::SetField<uint16_t>(location, value)
    #define SetAlignedBE_uint32_t(location, value) FieldAccessBE::SetField<uint32_t>(location, value)
    #define SetAlignedBE_uint64_t(location, value) FieldAccessBE::SetField<uint64_t>(location, value)
    #define SetAlignedBE_float(location, value) FieldAccessBE::SetField<float>(location, value)
    #define SetAlignedBE_double(location, value) FieldAccessBE::SetField<double>(location, value)
#else
    // #defines to access native endian aligned fields directly.
    #define GetAlignedBE_int8_t(location) FieldAccessAlignedNativeEndian::GetField<int8_t>(location)
    #define GetAlignedBE_int16_t(location) FieldAccessAlignedNativeEndian::GetField<int16_t>(location)
    #define GetAlignedBE_int32_t(location) FieldAccessAlignedNativeEndian::GetField<int32_t>(location)
    #define GetAlignedBE_int64_t(location) FieldAccessAlignedNativeEndian::GetField<int64_t>(location)
    #define GetAlignedBE_uint8_t(location) FieldAccessAlignedNativeEndian::GetField<uint8_t>(location)
    #define GetAlignedBE_uint16_t(location) FieldAccessAlignedNativeEndian::GetField<uint16_t>(location)
    #define GetAlignedBE_uint32_t(location) FieldAccessAlignedNativeEndian::GetField<uint32_t>(location)
    #define GetAlignedBE_uint64_t(location) FieldAccessAlignedNativeEndian::GetField<uint64_t>(location)
    #define GetAlignedBE_float(location) FieldAccessAlignedNativeEndian::GetField<float>(location)
    #define GetAlignedBE_double(location) FieldAccessAlignedNativeEndian::GetField<double>(location)

    #define SetAlignedBE_int8_t(location, value) FieldAccessAlignedNativeEndian::SetField<int8_t>(location, value)
    #define SetAlignedBE_int16_t(location, value) FieldAccessAlignedNativeEndian::SetField<int16_t>(location, value)
    #define SetAlignedBE_int32_t(location, value) FieldAccessAlignedNativeEndian::SetField<int32_t>(location, value)
    #define SetAlignedBE_int64_t(location, value) FieldAccessAlignedNativeEndian::SetField<int64_t>(location, value)
    #define SetAlignedBE_uint8_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint8_t>(location, value)
    #define SetAlignedBE_uint16_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint16_t>(location, value)
    #define SetAlignedBE_uint32_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint32_t>(location, value)
    #define SetAlignedBE_uint64_t(location, value) FieldAccessAlignedNativeEndian::SetField<uint64_t>(location, value)
    #define SetAlignedBE_float(location, value) FieldAccessAlignedNativeEndian::SetField<float>(location, value)
    #define SetAlignedBE_double(location, value) FieldAccessAlignedNativeEndian::SetField<double>(location, value)
    
    // #defines to access non-native endian aligned fields, using the unaligned
    // access functions to copy them a byte at a time.
    #define GetAlignedLE_int8_t(location) FieldAccessLE::GetField<int8_t>(location)
    #define GetAlignedLE_int16_t(location) FieldAccessLE::GetField<int16_t>(location)
    #define GetAlignedLE_int32_t(location) FieldAccessLE::GetField<int32_t>(location)
    #define GetAlignedLE_int64_t(location) FieldAccessLE::GetField<int64_t>(location)
    #define GetAlignedLE_uint8_t(location) FieldAccessLE::GetField<uint8_t>(location)
    #define GetAlignedLE_uint16_t(location) FieldAccessLE::GetField<uint16_t>(location)
    #define GetAlignedLE_uint32_t(location) FieldAccessLE::GetField<uint32_t>(location)
    #define GetAlignedLE_uint64_t(location) FieldAccessLE::GetField<uint64_t>(location)
    #define GetAlignedLE_float(location) FieldAccessLE::GetField<float>(location)
    #define GetAlignedLE_double(location) FieldAccessLE::GetField<double>(location)

    #define SetAlignedLE_int8_t(location, value) FieldAccessLE::SetField<int8_t>(location, value)
    #define SetAlignedLE_int16_t(location, value) FieldAccessLE::SetField<int16_t>(location, value)
    #define SetAlignedLE_int32_t(location, value) FieldAccessLE::SetField<int32_t>(location, value)
    #define SetAlignedLE_int64_t(location, value) FieldAccessLE::SetField<int64_t>(location, value)
    #define SetAlignedLE_uint8_t(location, value) FieldAccessLE::SetField<uint8_t>(location, value)
    #define SetAlignedLE_uint16_t(location, value) FieldAccessLE::SetField<uint16_t>(location, value)
    #define SetAlignedLE_uint32_t(location, value) FieldAccessLE::SetField<uint32_t>(location, value)
    #define SetAlignedLE_uint64_t(location, value) FieldAccessLE::SetField<uint64_t>(location, value)
    #define SetAlignedLE_float(location, value) FieldAccessLE::SetField<float>(location, value)
    #define SetAlignedLE_double(location, value) FieldAccessLE::SetField<double>(location, value)
#endif

#endif
