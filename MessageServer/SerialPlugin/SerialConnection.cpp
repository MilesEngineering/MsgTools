#include "SerialConnection.h"
#include "Cpp/Serial.h"
#include "qextserialport/src/qextserialenumerator.h"
#include <QDebug>
#include <QRadioButton>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>

SerialConnection::SerialConnection()
: ServerPort("Serial"),
  tmpRxHdr(),
  gotHeader(false),
  serialPort(),
  _settings("MsgTools", "MessageServer_SerialPlugin")
{
    /** \note Needs to be 57600, 8N1 for 3dr radio. */
    serialPort.setBaudRate(BAUD57600);
    serialPort.setFlowControl(FLOW_OFF);
    serialPort.setParity(PAR_NONE);
    serialPort.setDataBits(DATA_8);
    serialPort.setStopBits(STOP_1);

    startSequence = tmpRxHdr.GetStartSequence();

    _buttonGroup = new QGroupBox();
    QHBoxLayout* layout = new QHBoxLayout();
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
    _buttonGroup->setLayout(layout);

    connect(&serialPort, SIGNAL(readyRead()), this, SLOT(SerialDataReady()));
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
        }

        if(foundStart)
        {
            if(serialPort.bytesAvailable() > 0 && unsigned(serialPort.bytesAvailable()) >= sizeof(tmpRxHdr))
            {
                serialPort.read((char*)&tmpRxHdr, sizeof(tmpRxHdr));
                if(tmpRxHdr.GetStartSequence() == startSequence)
                {
                    /** \todo Review how checksums work.  Can we get location of header checksum, and stop counting before we reach it? */
                    uint16_t headerChecksum = 0;
                    for(int i=0; i<SerialHeader::SIZE; i++)
                        headerChecksum += ((uint8_t*)&tmpRxHdr)[i];

                    uint16_t headerChecksumInMessage = tmpRxHdr.GetHeaderChecksum();
                    int headerChecksumDoubleBookingEffect =
                            (0xFF & headerChecksumInMessage) +
                            (headerChecksumInMessage >> 8);
                    headerChecksum -= headerChecksumDoubleBookingEffect;

                    uint16_t bodyChecksumInMessage = tmpRxHdr.GetBodyChecksum();
                    int bodyChecksumDoubleBookingEffect =
                            (0xFF & bodyChecksumInMessage) +
                            (bodyChecksumInMessage >> 8);
                    headerChecksum -= bodyChecksumDoubleBookingEffect;

                    if(headerChecksum == tmpRxHdr.GetHeaderChecksum())
                    {
                        gotHeader = true;
                    }
                    else
                    {
                        qDebug() << "Error in serial parser.  HeaderChecksum " << headerChecksum << " != " << tmpRxHdr.GetHeaderChecksum();
                    }
                }
                else
                {
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
            }
            else
            {
                gotHeader = false;
                SerialMsgSlot(msg);
            }
        }
    }
}

void SerialConnection::MessageSlot(QSharedPointer<Message> msg)
{
    QSharedPointer<SerialMessage> serialMsg(SerialMessage::New(msg->hdr.GetLength()));
    serialMsg->hdr.SetPriority(msg->hdr.GetPriority());
    serialMsg->hdr.SetLength(msg->hdr.GetLength());
    serialMsg->hdr.SetDestination(msg->hdr.GetDestination());
    serialMsg->hdr.SetSource(msg->hdr.GetSource());

    uint16_t headerChecksum = 0;
    for(int i=0; i<SerialHeader::SIZE; i++)
        headerChecksum += ((uint8_t*)&serialMsg->hdr)[i];
    serialMsg->hdr.SetHeaderChecksum(headerChecksum);

    uint16_t bodyChecksum = 0;
    for(unsigned i=0; i<msg->hdr.GetLength(); i++)
        bodyChecksum += serialMsg->GetDataPtr()[i];
    serialMsg->hdr.SetBodyChecksum(headerChecksum);

    memcpy(serialMsg->GetDataPtr(), msg->GetDataPtr(), msg->hdr.GetLength());

    TransmitSerialMsg(serialMsg);
}

void SerialConnection::TransmitSerialMsg(QSharedPointer<SerialMessage> msg)
{
    serialPort.write((char*)msg->RawBuffer(), msg->GetTotalLength());
}

void SerialConnection::SerialMsgSlot(QSharedPointer<SerialMessage> msg)
{
    QSharedPointer<Message> dbmsg (Message::New(msg->hdr.GetLength()));

    dbmsg->hdr.SetPriority(msg->hdr.GetPriority());
    dbmsg->hdr.SetDestination(msg->hdr.GetDestination());
    dbmsg->hdr.SetSource(msg->hdr.GetSource());
    dbmsg->hdr.SetID(msg->hdr.GetID());

    memcpy(dbmsg->GetDataPtr(), msg->GetDataPtr(), msg->hdr.GetLength());
    emit MsgSignal(dbmsg);
}

QWidget* SerialConnection::widget(int index)
{
    if(index == 2)
    {
        return _buttonGroup;
    }
    return ServerPort::widget(index);
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
