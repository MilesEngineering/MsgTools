#ifndef MSGTOOLS_MESSAGE_H
#define MSGTOOLS_MESSAGE_H

#include <QObject>
#include <stdint.h>
#include <assert.h>

#include "FieldInfo.h"
#include "MsgInfo.h"

#define UNDEFINED_MSGID (-1)

#define MessageIdType uint64_t

#include <Cpp/headers/NetworkHeader.h>

template <class HeaderClass>
class HeaderWrapper : public HeaderClass
{
    public:
        HeaderWrapper()
        : HeaderClass()
        {
        }
        void InitializeTime()
        {
            /** \todo How to set 32-bit rolling ms counter?
                      Or absolute timestamp as uint64, float64? */
            SetTime(0);
        }
        void SetTime(uint32_t time)
        {
            SetTime(time);
        }
        uint32_t GetTime()
        {
            return GetTime();
        }

    private:
#ifdef ENABLE_REFLECTION
        static const FieldInfo* fieldInfo(const QString& name)
        {
            return HeaderClass::ReflectionInfo()->GetField(name);
        }
#endif
};

typedef HeaderWrapper<NetworkHeader> NetworkHeaderWrapper;

// This is a C++ implementation of a message.
// It doesn't use Qt or pool allocated messages, but does use the C++ stdlib's vector type to store data.

// Because we don't use a pool allocator, we don't want to define MessageBuffer,
// and Exists() always returns true.
// We still need to define the Message constructor that accepts a MessageBuffer* as
// a parameter, because generated code calls it, if anyone gives a MessageBuffer*
// as a constructor parameter of the generated classes.  This could be eliminated
// if we made a new C++ generated code template file that didn't mention MessageBuffer.
typedef void MessageBuffer;

class Message
{
    public:
        Message(uint16_t len)
        {
            hdr.SetDataLength(len);
            m_data.reserve(len);
            m_data.insert(m_data.begin(), len, '\0');
        }
        Message(MessageBuffer* buf);
        static Message* New(uint16_t datalen)
        {
            return new Message(datalen);
        }
        void CopyHdr(Message& rhs)
        {
            memcpy(&hdr, &rhs.hdr, sizeof(hdr));
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
        uint8_t* GetDataPtr() { return &m_data[0]; }
        uint16_t GetDataLength()
        {
            return hdr.GetDataLength();
        }
        void SetDataLength(int len)
        {
            hdr.SetDataLength(len);
        }
        void SetMessageID(uint32_t id)
        {
            hdr.SetMessageID(id);
        }
        uint32_t GetMessageID()
        {
            return hdr.GetMessageID();
        }
        bool Exists() {return true;}
        void InitializeTime()
        {
            hdr.InitializeTime();
        }
    public:
        NetworkHeaderWrapper hdr;
        std::vector<uint8_t>  m_data;
};

#endif
