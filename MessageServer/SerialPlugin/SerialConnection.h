#ifndef SERIAL_CONNECTION_H__
#define SERIAL_CONNECTION_H__

#include <QSettings>
#include "MessageServer/ServerPort.h"
#include "SerialMessage.h"
#include <QSerialPort>
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
        void BaudrateChanged(bool pressed);
        void PrintDebugInfo();
        QWidget* widget(int index) override;
    private:
        SerialHeaderWrapper tmpRxHdr;
        bool gotHeader;
        QSerialPort serialPort;
        QGroupBox _buttonGroup;
        QSettings _settings;
        QLabel _statusLabel;
        int _rxMsgCount;
        int _rxStartErrorCount;
        int _rxHeaderErrorCount;
        int _rxBodyErrorCount;
        uint16_t  _timestampOffset;
        uint16_t  _lastTimestamp;
        QDateTime _lastWrapTime;
        void radioButtonToggled(bool pressed);
        enum RxErrorType { START, HEADER, BODY };
        void gotRxError(RxErrorType errorType);
        QList<QPair<const FieldInfo*, const FieldInfo*> > correspondingFields;
};

#endif

