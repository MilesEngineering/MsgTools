#ifndef MESSAGE_H__
#define MESSAGE_H__

#include <QObject>
#include <stdint.h>
#include <assert.h>

#include "Cpp/headers/NetworkHeader.h"

#define MsgHeader NetworkHeader

class Message
{
    public:
        Message()
        {
            Allocate(0);
            hdr->SetLength(0);
        }
        Message(uint16_t len)
        {
            Allocate(len);
            hdr->SetLength(len);
        }
        void Allocate(uint16_t datalen)
        {
            uint8_t* buffer = new uint8_t[sizeof(Message)+datalen];
            hdr = (MsgHeader*)buffer;
            hdr->Init();
            m_data = (uint8_t*)&hdr[1];
        }
        uint8_t* GetDataPtr() { return m_data; }
        void SetPayloadLength(int len) { hdr->SetLength(len); }
        void SetMessageID(uint32_t id) { hdr->SetID(id); }
        uint32_t GetMessageID() { return hdr->GetID(); }
        bool Exists() { return hdr != 0 && m_data != 0; }
        void InitializeTime()
        {
            /** \todo How to set 32-bit rolling ms counter? */
            hdr->SetTime(0);
        }
    public:
        MsgHeader* hdr;
        uint8_t* m_data;
};

#endif
