#ifndef SERIAL_CONNECTION_H__
#define SERIAL_CONNECTION_H__

#include <QSettings>
#include "MessageServer/ServerPort.h"
#include "SerialMessage.h"
#include "qextserialport/src/qextserialport.h"
#include <QGroupBox>
#include <QDateTime>

class SerialConnection : public ServerPort
{
    Q_OBJECT
    public:
        SerialConnection();
        virtual ~SerialConnection();
    public slots:
        virtual void MessageSlot(QSharedPointer<Message> msg);
        virtual void SerialMsgSlot(QSharedPointer<SerialMessage> msg);
        virtual void SerialDataReady();
        QWidget* widget(int index) override;
    private:
        SerialHeader tmpRxHdr;
        bool gotHeader;
        uint32_t startSequence;
        QextSerialPort serialPort;
        QGroupBox _buttonGroup;
        QSettings _settings;
        QLabel _statusLabel;
        int _rxMsgCount;
        int _rxErrorCount;
        uint16_t  _timestampOffset;
        uint16_t  _lastTimestamp;
        QDateTime _lastTime;
        QDateTime _lastWrapTime;
        void radioButtonToggled(bool pressed);
        void gotRxError();
};

#endif

