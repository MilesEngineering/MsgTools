#ifndef MSGTOOLS_MESSAGE_H
#define MSGTOOLS_MESSAGE_H

#include <QObject>
#include <stdint.h>
#include <assert.h>

#include "FieldInfo.h"
#include "MsgInfo.h"

#define UNDEFINED_MSGID (-1)

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
            /** \todo How to set 32-bit rolling ms counter? */
            if(fieldInfo("Time"))
                fieldInfo("Time")->SetValue(QString("%1").arg(0), HeaderClass::m_data);
        }
        void SetTime(uint32_t time)
        {
            if(fieldInfo("Time"))
                fieldInfo("Time")->SetValue(QString("%1").arg(time), HeaderClass::m_data);
        }
        uint32_t GetTime()
        {
            if(fieldInfo("Time"))
                return fieldInfo("Time")->Value(HeaderClass::m_data).toInt();
            return 0;
        }

    private:
        static const FieldInfo* fieldInfo(const QString& name)
        {
            return HeaderClass::ReflectionInfo()->GetField(name);
        }
};

typedef HeaderWrapper<NetworkHeader> NetworkHeaderWrapper;

class Message
{
    public:
        Message(uint16_t len)
        {
            hdr.SetDataLength(len);
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
