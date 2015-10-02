#include "SerialConnection.h"
#include "Cpp/SerialHeader.h"
#include "qextserialport/src/qextserialenumerator.h"
#include <QDebug>
#include <QRadioButton>
#include <QHBoxLayout>
#include <QLabel>

SerialConnection::SerialConnection()
: ServerPort("Serial"),
  tmpRxHdr(),
  gotHeader(false),
  serialPort(),
  _buttonGroup(),
  _settings("MsgTools", "MessageServer_SerialPlugin"),
  _statusLabel(""),
  _rxMsgCount(0),
  _rxErrorCount(0),
  _timestampOffset(0),
  _lastTimestamp(0),
  _lastTime(),
  _lastWrapTime()
{
    /** \note Needs to be 57600, 8N1 for 3dr radio. */
    serialPort.setBaudRate(BAUD57600);
    serialPort.setFlowControl(FLOW_OFF);
    serialPort.setParity(PAR_NONE);
    serialPort.setDataBits(DATA_8);
    serialPort.setStopBits(STOP_1);

    startSequence = tmpRxHdr.GetStartSequence();

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
        /** \todo Synchronize on start character */
        while(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(startSequence))
        {
            /** peek at first byte.
             * if it's start byte, break.
             * else, throw it away and try again. */
            serialPort.peek((char*)&tmpRxHdr, sizeof(startSequence));
            if(tmpRxHdr.GetStartSequence() == startSequence)
            {
                foundStart = true;
                break;
            }
            uint8_t throwAway;
            serialPort.read((char*)&throwAway, sizeof(throwAway));
            gotRxError();
        }

        if(foundStart)
        {
            if(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(tmpRxHdr))
            {
                serialPort.read((char*)&tmpRxHdr, sizeof(tmpRxHdr));
                if(tmpRxHdr.GetStartSequence() == startSequence)
                {
                    /** \note Stop counting before we reach header checksum location. */
                    uint16_t headerChecksum = 0;
                    for(int i=0; i<SerialHeader::HeaderChecksumFieldInfo::loc; i++)
                        headerChecksum += ((uint8_t*)&tmpRxHdr)[i];

                    if(headerChecksum == tmpRxHdr.GetHeaderChecksum())
                    {
                        gotHeader = true;
                    }
                    else
                    {
                        gotRxError();
                        qDebug() << "Error in serial parser.  HeaderChecksum " << headerChecksum << " != " << tmpRxHdr.GetHeaderChecksum();
                    }
                }
                else
                {
                    gotRxError();
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

            uint16_t bodyChecksum = 0;
            for(unsigned i=0; i<msg->hdr.GetLength(); i++)
                bodyChecksum += msg->GetDataPtr()[i];

            if(tmpRxHdr.GetBodyChecksum() != bodyChecksum)
            {
                qDebug() << "Error in serial parser.  BodyChecksum " << bodyChecksum << " != " << tmpRxHdr.GetBodyChecksum();
                gotHeader = false;
                gotRxError();
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

        uint16_t headerChecksum = 0;
        for(int i=0; i<SerialHeader::SIZE; i++)
            headerChecksum += ((uint8_t*)&serialHdr)[i];
        serialHdr.SetHeaderChecksum(headerChecksum);

        uint16_t bodyChecksum = 0;
        for(unsigned i=0; i<msg->hdr.GetLength(); i++)
            bodyChecksum += msg->GetDataPtr()[i];
        serialHdr.SetBodyChecksum(bodyChecksum);

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
    _lastTime = thisTime;
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

void SerialConnection::gotRxError()
{
    _rxErrorCount++;
    _statusLabel.setText(QString("Error: %1, Msg: %2").arg(_rxErrorCount).arg(_rxMsgCount));
}
