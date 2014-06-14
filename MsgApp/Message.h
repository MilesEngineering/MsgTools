#ifndef MESSAGE_H__
#define MESSAGE_H__

#include <QObject>
#include <stdint.h>
#include <qendian.h>
#include <assert.h>

#include "obj/Cpp/Network.h"

#define MsgHeader NetworkHeader

class Message
{
    private:
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
        uint8_t* GetDataPtr() { return (uint8_t*)(&hdr+1); }
    public:
        MsgHeader hdr;
};

#endif
