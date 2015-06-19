#ifndef __DATABUS_MESSAGE_H__
#define __DATABUS_MESSAGE_H__

#include <QObject>
#include <stdint.h>
#include <qendian.h>
#include <assert.h>

#define NEED_TO_SWAP_ENDIAN_OF_FIELDS
inline void Swap(uint16_t* x) {*x = qFromBigEndian<quint16>(*x); }
inline void Swap(uint32_t* x) {*x = qFromBigEndian<quint32>(*x); }
inline void Swap(uint64_t* x) {*x = qFromBigEndian<quint64>(*x); }

#include <Cpp/Network.h>

class Message
{
    private:
        // private constructor
        Message(uint16_t len)
        {
            hdr.SetLength(len);
        }
    public:
        static Message* New(uint16_t datalen)
        {
            uint8_t* buffer = new uint8_t[sizeof(Message)+datalen];
            Message* dbmsg = new(buffer) Message(datalen);
            return dbmsg;
        }
        void CopyHdr(Message& rhs)
        {
            memcpy(&hdr, &rhs.hdr, sizeof(hdr));
        }
        void SwapHeader()
        {
/** \todo do we need to support non-native endian?  if so, we have to add it to the code generator
            hdr.EndianSwapBody();*/
        }

        ~Message()
        {
        }
        static int HeaderSize()
        {
            return sizeof(hdr);
        }
        uint8_t* RawBuffer()
        {
            return (uint8_t*)&hdr;
        }
        uint8_t* GetDataPtr() { return (uint8_t*)(&hdr+1); }
        uint16_t GetTotalLength()
        {
            return hdr.GetLength();
        }
    public:
        NetworkHeader hdr;
};

#endif

