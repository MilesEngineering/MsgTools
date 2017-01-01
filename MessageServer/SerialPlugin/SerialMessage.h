#ifndef SERIAL_MESSAGE_H
#define SERIAL_MESSAGE_H

#include "Cpp/headers/SerialHeader.h"

typedef HeaderWrapper<SerialHeader> SerialHeaderWrapper;

class SerialMessage
{
    private:
        SerialMessage(uint16_t len)
        {
            hdr.SetDataLength(len);
            data.reserve(len);
            data.insert(data.begin(), len, '\0');
        }
    public:
        static SerialMessage* New(uint16_t datalen)
        {
            return new SerialMessage(datalen);
        }

        ~SerialMessage()
        {
        }

        uint8_t* RawBuffer()
        {
            return (uint8_t*)&hdr;
        }
        uint8_t* GetDataPtr() { return &data[0]; }
    public:
        SerialHeaderWrapper hdr;
    private:
        std::vector<uint8_t> data;
};

#endif // SERIAL_MESSAGE_H
