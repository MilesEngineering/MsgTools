#ifndef SERIAL_MESSAGE_H
#define SERIAL_MESSAGE_H

#include "Cpp/Serial.h"

class SerialMessage
{
    private:
        SerialMessage(uint16_t len)
        {
            hdr.SetLength(len);
        }
    public:
        static SerialMessage* New(uint16_t datalen)
        {
            uint8_t* buffer = new uint8_t[sizeof(SerialMessage)+datalen];
            SerialMessage* serialMsg = new(buffer) SerialMessage(datalen);
            return serialMsg;
        }

        ~SerialMessage()
        {
#if 0
            printf("destructing a serial message\n");
#endif
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
        SerialHeader hdr;
};

#endif // SERIAL_MESSAGE_H
