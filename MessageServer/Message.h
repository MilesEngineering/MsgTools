#ifndef __DATABUS_MESSAGE_H__
#define __DATABUS_MESSAGE_H__

#include <QObject>
#include <stdint.h>
#include <assert.h>

#include <Cpp/Network.h>

class Message
{
    public:
        Message(uint16_t len)
        {
            hdr.SetLength(len);
            m_data.reserve(len);
            m_data.insert(m_data.begin(), len, '\0');
        }
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
        uint16_t GetTotalLength()
        {
            return hdr.GetLength();
        }
        void SetPayloadLength(int len) { hdr.SetLength(len); }
        void SetMessageID(uint32_t id) { hdr.SetID(id); }
        bool Exists() {return true;}
        void InitializeTime()
        {
            /** \todo How to set 32-bit rolling ms counter? */
            hdr.SetTime(0);
        }
    public:
        NetworkHeader hdr;
        std::vector<uint8_t>  m_data;
};

#endif

