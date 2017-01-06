#include "SerialConnection.h"
#include "qextserialport/src/qextserialenumerator.h"
#include <QDebug>
#include <QRadioButton>
#include <QHBoxLayout>
#include <QLabel>
#include <QTimer>

uint16_t Crc(const uint8_t* data, int length)
{
    uint16_t crc = 0;
    for (int i = 0; i<length; i++)
    {
        crc = (crc >> 8) | (crc << 8);
        crc ^= data[i];
        crc ^= (crc & 0xff) >> 4;
        crc ^= crc << 12;
        crc ^= (crc & 0xff) << 5;
    }
    return crc;
}

SerialConnection::SerialConnection()
: ServerPort("Serial"),
  tmpRxHdr(),
  gotHeader(false),
  serialPort(),
  _buttonGroup(),
  _settings("MsgTools", "MessageServer_SerialPlugin"),
  _statusLabel(""),
  _rxMsgCount(0),
  _rxStartErrorCount(0),
  _rxHeaderErrorCount(0),
  _rxBodyErrorCount(0),
  _timestampOffset(0),
  _lastTimestamp(0),
  _lastWrapTime()
{
    /** \note Set subscription mask to accept all messages. */
    subscriptionMask = 0;

    /** \note Needs to be 57600, 8N1 for 3dr radio. */
    serialPort.setBaudRate(BAUD115200);
    serialPort.setFlowControl(FLOW_OFF);
    serialPort.setParity(PAR_NONE);
    serialPort.setDataBits(DATA_8);
    serialPort.setStopBits(STOP_1);

    _buttonGroup.setStyleSheet("border:0;");

    QGroupBox* buttonGroup1 = new QGroupBox;
    buttonGroup1->setStyleSheet("border:0;");
    QHBoxLayout* layout1 = new QHBoxLayout();
    layout1->addWidget(&_statusLabel);
    QString lastconnection = _settings.value("LastSerialPortUsed", "").toString();
#ifndef WIN32
    layout1->addWidget(new QLabel("/dev/"));
    qDebug() << "Looking for /dev/ttyUSB*, ttyS*, ttyACM0, COM *ONLY*!";
    const QStringList acceptableNames = QStringList() << "USB" << "ttyS" << "ACM0" << "COM";
#endif
    foreach (QextPortInfo info, QextSerialEnumerator::getPorts())
    {
#ifndef WIN32
        /** \todo Restrict list of UARTs to the below selection */
        bool found = false;
        foreach(QString acceptableName, acceptableNames)
        {
            if(info.portName.contains(acceptableName))
            {
                found = true;
            }
        }
        if(found)
#endif
        {
            QString name = info.portName;
            qDebug() << "Found port " << info.portName << " at " << info.physName;
            QRadioButton* rb = new QRadioButton(name);
            connect(rb, &QRadioButton::toggled, this, &SerialConnection::radioButtonToggled);
            layout1->addWidget(rb);
            if(lastconnection == info.portName)
                rb->click();
        }
    }
    buttonGroup1->setLayout(layout1);

    QGroupBox* buttonGroup2 = new QGroupBox;
    buttonGroup2->setStyleSheet("border:0;");
    QHBoxLayout* layout2 = new QHBoxLayout();

    QStringList speeds = QStringList() << "57.6" << "115.2";
    QString lastSpeed = _settings.value("LastSerialPortSpeedUsed", "").toString();
    foreach(QString speed, speeds)
    {

        QRadioButton* baudRate  = new QRadioButton(speed);
        layout2->addWidget(baudRate);
        connect(baudRate, &QRadioButton::toggled, this, &SerialConnection::BaudrateChanged);
        if(lastSpeed == speed)
            baudRate->click();
    }
    buttonGroup2->setLayout(layout2);

    QHBoxLayout* layout = new QHBoxLayout();
    layout->addWidget(buttonGroup1);
    layout->addWidget(buttonGroup2);
    _buttonGroup.setLayout(layout);
    
    QTimer* timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, &SerialConnection::PrintDebugInfo);
    timer->start(500);

    connect(&serialPort, &QextSerialPort::readyRead, this, &SerialConnection::SerialDataReady);

    // Make a list of fields in the serial header and network header that have matching names.
    foreach(const FieldInfo* serialFieldInfo, SerialHeaderWrapper::ReflectionInfo()->GetFields())
    {
        const FieldInfo* networkFieldInfo = NetworkHeader::ReflectionInfo()->GetField(serialFieldInfo->Name());
        if(networkFieldInfo)
            correspondingFields.append(QPair<const FieldInfo*, const FieldInfo*>(serialFieldInfo, networkFieldInfo));
    }
}

SerialConnection::~SerialConnection()
{
}

void SerialConnection::BaudrateChanged(bool pressed)
{
    if(pressed)
    {
        QRadioButton* button = dynamic_cast<QRadioButton*>(sender());
        if(button->text() == "57.6")
        {
            serialPort.setBaudRate(BAUD57600);
            qDebug() << "Setting baudrate " << button->text();
        }
        else if(button->text() == "115.2")
        {
            serialPort.setBaudRate(BAUD115200);
            qDebug() << "Setting baudrate " << button->text();
        }
        else
        {
            qDebug() << "Error, unknown baudrate " << button->text();
        }
        _settings.setValue("LastSerialPortSpeedUsed", button->text());
    }
}
void SerialConnection::SerialDataReady()
{
    if(!gotHeader)
    {
        bool foundStart = false;
        /** \note Synchronize on start sequence */
        while(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(SerialHeader::StartSequenceFieldInfo::defaultValue))
        {
            /** peek at start of message.
             * if it's start sequence, break.
             * else, throw it away and try again. */
            serialPort.peek((char*)&tmpRxHdr, sizeof(SerialHeader::StartSequenceFieldInfo::defaultValue));
            if(tmpRxHdr.GetStartSequence() == SerialHeader::StartSequenceFieldInfo::defaultValue)
            {
                foundStart = true;
                break;
            }
            uint8_t throwAway;
            serialPort.read((char*)&throwAway, sizeof(throwAway));
            gotRxError(START);
        }

        if(foundStart)
        {
            if(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(tmpRxHdr))
            {
                serialPort.read((char*)&tmpRxHdr, sizeof(tmpRxHdr));
                if(tmpRxHdr.GetStartSequence() == SerialHeader::StartSequenceFieldInfo::defaultValue)
                {
                    /** \note Stop counting before we reach header checksum location. */
                    uint16_t headerCrc = Crc((uint8_t*)&tmpRxHdr, SerialHeader::HeaderChecksumFieldInfo::loc);

                    if(headerCrc == tmpRxHdr.GetHeaderChecksum())
                    {
                        gotHeader = true;
                    }
                    else
                    {
                        gotRxError(HEADER);
                    }
                }
                else
                {
                    gotRxError(START);
                    qDebug() << "Error in serial parser.  Thought I had start byte, now it's gone!";
                }
            }
        }
    }

    if(gotHeader)
    {
        if(serialPort.bytesAvailable() >= tmpRxHdr.GetDataLength())
        {
            // allocate the serial message body, read from the serial port
            QSharedPointer<SerialMessage> msg(SerialMessage::New(tmpRxHdr.GetDataLength()));
            msg->hdr = tmpRxHdr;
            serialPort.read((char*)msg->GetDataPtr(), msg->hdr.GetDataLength());

            uint16_t bodyCrc = Crc(msg->GetDataPtr(), msg->hdr.GetDataLength());

            if(tmpRxHdr.GetBodyChecksum() != bodyCrc)
            {
                gotHeader = false;
                gotRxError(BODY);
            }
            else
            {
                gotHeader = false;
                _rxMsgCount++;
                SerialMsgSlot(msg);
            }
        }
    }
}

void SerialConnection::MessageSlot(QSharedPointer<Message> msg)
{
    if((msg->GetMessageID() & subscriptionMask) == subscriptionValue ||
        subscriptions.contains(msg->GetMessageID()))
    {
        SerialHeaderWrapper serialHdr;
        serialHdr.SetMessageID(msg->hdr.GetMessageID());
        // loop through fields using reflection, and transfer contents from
        // network message to serial message
        for(int i=0; i<correspondingFields.length(); i++)
        {
            QPair<const FieldInfo*,const FieldInfo*> pair = correspondingFields[i];
            const FieldInfo* serInfo = pair.first;
            const FieldInfo* netInfo = pair.second;
            serInfo->SetValue(netInfo->Value(msg->hdr.m_data), serialHdr.m_data);
        }

        uint16_t headerCrc = Crc((uint8_t*)&serialHdr, SerialHeader::HeaderChecksumFieldInfo::loc);
        serialHdr.SetHeaderChecksum(headerCrc);

        uint16_t bodyCrc = Crc(msg->GetDataPtr(), msg->hdr.GetDataLength());
        serialHdr.SetBodyChecksum(bodyCrc);

        serialPort.write((char*)&serialHdr, sizeof(serialHdr));
        serialPort.write((char*)msg->GetDataPtr(), msg->hdr.GetDataLength());
    }
}

void SerialConnection::SerialMsgSlot(QSharedPointer<SerialMessage> msg)
{
    QSharedPointer<Message> dbmsg (Message::New(msg->hdr.GetDataLength()));
    dbmsg->hdr.SetMessageID(msg->hdr.GetMessageID());

    // loop through fields using reflection, and transfer contents from
    // serial message to network message
    for(int i=0; i<correspondingFields.length(); i++)
    {
        QPair<const FieldInfo*, const FieldInfo*> pair = correspondingFields[i];
        const FieldInfo* serInfo = pair.first;
        const FieldInfo* netInfo = pair.second;
        netInfo->SetValue(serInfo->Value(msg->hdr.m_data), dbmsg->hdr.m_data);
    }
    
    /** \todo Detect time rolling */
    uint16_t thisTimestamp = msg->hdr.GetTime();
    QDateTime thisTime = QDateTime::currentDateTime();
    uint16_t timestampOffset = _timestampOffset;
    if(thisTimestamp < _lastTimestamp)
    {
        /** \note If the timestamp shouldn't have wrapped yet, assume messages sent out-of-order,
             and do not wrap again. */
        if(thisTime > _lastWrapTime.addSecs(30))
        {
            _lastWrapTime = thisTime;
            _timestampOffset++;
            timestampOffset = _timestampOffset;
        }
    }
    _lastTimestamp = thisTimestamp;
    dbmsg->hdr.SetTime((timestampOffset << 16) + thisTimestamp);

    memcpy(dbmsg->GetDataPtr(), msg->GetDataPtr(), msg->hdr.GetDataLength());
    emit MsgSignal(dbmsg);
}

QWidget* SerialConnection::widget(int index)
{
    switch(index)
    {
        case 0:
            return &removeClient;
        case 1:
            return &statusLabel;
        case 2:
            return &_buttonGroup;
        default:
            return 0;
    }
}

void SerialConnection::radioButtonToggled(bool pressed)
{
    QRadioButton* rb = dynamic_cast<QRadioButton*>(sender());
    if(pressed)
    {
#ifdef WIN32
        const QString portName(rb->text());
#else
        const QString portName(QString("/dev/") + rb->text());
#endif
        serialPort.setPortName(portName);
        if(serialPort.open(QextSerialPort::ReadWrite))
        {
            qDebug() << "Opened " << portName << endl;
            _settings.setValue("LastSerialPortUsed", portName);
        }
        else
            qWarning() << "Couldn't open " << portName << endl;
    }
}

void SerialConnection::gotRxError(RxErrorType errorType)
{
    switch(errorType)
    {
        case START:
            _rxStartErrorCount++;
            break;
        case HEADER:
            _rxHeaderErrorCount++;
            break;
        case BODY:
            _rxBodyErrorCount++;
            break;
    }
}
void SerialConnection::PrintDebugInfo()
{
    _statusLabel.setText(QString("Errors: %1, %2, %3, Msg: %4").arg(_rxStartErrorCount).arg(_rxHeaderErrorCount).arg(_rxBodyErrorCount).arg(_rxMsgCount));
}
