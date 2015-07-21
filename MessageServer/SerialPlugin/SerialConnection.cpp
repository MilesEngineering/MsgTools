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
  serialPort(),
  _settings("MsgTools", "MessageServer_SerialPlugin")
{
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
    // allocate temporary header
    SerialHeader hdr;

    /** \todo Synchronize on start character */
    serialPort.read((char*)&hdr, sizeof(hdr));

    // allocate the serial message body, read from the serial port
    QSharedPointer<SerialMessage> msg(SerialMessage::New(msg->hdr.GetLength()));
    msg->hdr = hdr;
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
