#ifndef SERIAL_CONNECTION_H__
#define SERIAL_CONNECTION_H__

#include <QSettings>
#include "MessageServer/ServerPort.h"
#include "SerialMessage.h"
#include "qextserialport/src/qextserialport.h"

class QGroupBox;

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
        QWidget* widget(int index) override;
    private:
        SerialHeader tmpRxHdr;
        bool gotHeader;
        uint32_t startSequence;
        QextSerialPort serialPort;
        QGroupBox* _buttonGroup;
        QSettings _settings;
        void radioButtonToggled(bool pressed);
};

#endif

