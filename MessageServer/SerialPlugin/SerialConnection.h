#ifndef SERIAL_CONNECTION_H__
#define SERIAL_CONNECTION_H__

#include "MessageServer/ServerPort.h"
#include "SerialMessage.h"
#include "qextserialport/src/qextserialport.h"

class SerialConnection : public ServerPort
{
    Q_OBJECT
    public:
        SerialConnection();
    public slots:
        virtual void MessageSlot(QSharedPointer<Message> msg);
        virtual void SerialMsgSlot(QSharedPointer<SerialMessage> msg);
        virtual void SerialDataReady();
        void TransmitSerialMsg(QSharedPointer<SerialMessage> msg);
    private:
        QextSerialPort serialPort;
};

#endif

