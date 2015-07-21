#include "SerialConnection.h"
#include "Cpp/Serial.h"
#include "qextserialport/src/qextserialenumerator.h"
#include <QDebug>

SerialConnection::SerialConnection()
: ServerPort("Serial"),
  serialPort()
{
    foreach (QextPortInfo info, QextSerialEnumerator::getPorts())
    {
        if(info.portName.contains("USB"))
            qDebug() << "Found port " << info.portName << " at " << info.physName;
    }
    const QString portName("/dev/ttyUSB0");
    serialPort.setPortName(portName);
    if(serialPort.open(QextSerialPort::ReadWrite))
        qDebug() << "Opened " << portName << endl;
    else
        qWarning() << "Couldn't open " << portName << endl;

    connect(&serialPort, SIGNAL(readyRead()), this, SLOT(SerialDataReady()));
}

void SerialConnection::SerialDataReady()
{
    // allocate temporary header, read from serial port
    SerialHeader hdr;
    serialPort.read((char*)&hdr, sizeof(hdr));

    // allocate the serial message body, read from the serial port
    QSharedPointer<SerialMessage> msg(SerialMessage::New(msg->hdr.GetLength()));
    serialPort.read((char*)msg->GetDataPtr(), msg->hdr.GetLength());

    SerialMsgSlot(msg);
}

void SerialConnection::MessageSlot(QSharedPointer<Message> msg)
{
    QSharedPointer<SerialMessage> serialMsg(SerialMessage::New(msg->hdr.GetLength()));
    serialMsg->hdr.SetPriority(msg->hdr.GetPriority());
    serialMsg->hdr.SetLength(msg->hdr.GetLength());
    serialMsg->hdr.SetDestination(msg->hdr.GetDestination());
    serialMsg->hdr.SetSource(msg->hdr.GetSource());

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
