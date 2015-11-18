#include "SerialConnection.h"
#include "Cpp/headers/SerialHeader.h"
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
    /** \note Needs to be 57600, 8N1 for 3dr radio. */
    serialPort.setBaudRate(BAUD115200);
    serialPort.setFlowControl(FLOW_OFF);
    serialPort.setParity(PAR_NONE);
    serialPort.setDataBits(DATA_8);
    serialPort.setStopBits(STOP_1);

    _buttonGroup.setStyleSheet("border:0;");
    QHBoxLayout* layout = new QHBoxLayout();
    layout->addWidget(&_statusLabel);
    layout->addWidget(new QLabel("/dev/"));
    qDebug() << "Looking for /dev/ttyUSB* and /dev/ttyACM0 *ONLY*!";
    QString lastconnection = _settings.value("LastSerialPortUsed", "").toString();
    foreach (QextPortInfo info, QextSerialEnumerator::getPorts())
    {
        /** \todo Restrict list of UARTs to the below selection */
        if(info.portName.contains("USB") || info.portName.contains("ACM0"))
        {
            QString name = info.portName;
            //qDebug() << "Found port " << info.portName << " at " << info.physName;
            QRadioButton* rb = new QRadioButton(name);
            connect(rb, &QRadioButton::toggled, this, &SerialConnection::radioButtonToggled);
            layout->addWidget(rb);
            if(lastconnection == info.physName)
                rb->click();
        }
    }
    _buttonGroup.setLayout(layout);
    
    QTimer* timer = new QTimer(this);
    connect(timer, SIGNAL(timeout()), this, SLOT(PrintDebugInfo()));
    timer->start(500);

    connect(&serialPort, SIGNAL(readyRead()), this, SLOT(SerialDataReady()));
}

SerialConnection::~SerialConnection()
{
}

void SerialConnection::SerialDataReady()
{
    if(!gotHeader)
    {
        bool foundStart = false;
        /** \note Synchronize on start sequence */
        while(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(SerialHeader::StartSequenceFieldInfo::defaultValue))
        {
            /** peek at first byte.
             * if it's start byte, break.
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
                        qDebug() << "Error in serial parser.  HeaderChecksum " << headerCrc << " != " << tmpRxHdr.GetHeaderChecksum();
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
        if(serialPort.bytesAvailable() >= tmpRxHdr.GetLength())
        {
            // allocate the serial message body, read from the serial port
            QSharedPointer<SerialMessage> msg(SerialMessage::New(tmpRxHdr.GetLength()));
            msg->hdr = tmpRxHdr;
            serialPort.read((char*)msg->GetDataPtr(), msg->hdr.GetLength());

            uint16_t bodyCrc = Crc(msg->GetDataPtr(), msg->hdr.GetLength());

            if(tmpRxHdr.GetBodyChecksum() != bodyCrc)
            {
                qDebug() << "Error in serial parser.  BodyChecksum " << bodyCrc << " != " << tmpRxHdr.GetBodyChecksum();
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
    if(msg->hdr.GetID() < 0xFFFF)
    {
        SerialHeader serialHdr;
        serialHdr.SetID(msg->hdr.GetID());
        serialHdr.SetPriority(msg->hdr.GetPriority());
        serialHdr.SetLength(msg->hdr.GetLength());
        serialHdr.SetDestination(msg->hdr.GetDestination());
        serialHdr.SetSource(msg->hdr.GetSource());

        uint16_t headerCrc = Crc((uint8_t*)&serialHdr, SerialHeader::SIZE);
        serialHdr.SetHeaderChecksum(headerCrc);

        uint16_t bodyCrc = Crc(msg->GetDataPtr(), msg->hdr.GetLength());
        serialHdr.SetBodyChecksum(bodyCrc);

        serialPort.write((char*)&serialHdr, sizeof(serialHdr));
        serialPort.write((char*)msg->GetDataPtr(), msg->hdr.GetLength());
    }
}

void SerialConnection::SerialMsgSlot(QSharedPointer<SerialMessage> msg)
{
    QSharedPointer<Message> dbmsg (Message::New(msg->hdr.GetLength()));

    dbmsg->hdr.SetPriority(msg->hdr.GetPriority());
    dbmsg->hdr.SetDestination(msg->hdr.GetDestination());
    dbmsg->hdr.SetSource(msg->hdr.GetSource());
    dbmsg->hdr.SetID(msg->hdr.GetID());
    
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

    memcpy(dbmsg->GetDataPtr(), msg->GetDataPtr(), msg->hdr.GetLength());
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
        const QString portName(QString("/dev/") + rb->text());
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
