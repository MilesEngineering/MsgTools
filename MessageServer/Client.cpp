#include "Client.h"

Client::Client(QTcpSocket* sock)
: ServerPort(sock->peerAddress().toString()),
  _tcpSocket(sock),
  _rxHeader(Message::New(0)),
  _receivedHeader(false)
{
    connect(sock, SIGNAL(readyRead()), this, SLOT(HandleIncomingPacket()));
    connect(_tcpSocket, SIGNAL(stateChanged(QAbstractSocket::SocketState)), this, SLOT(SocketStateChanged(QAbstractSocket::SocketState)));
    connect(_tcpSocket, SIGNAL(disconnected()), this, SLOT(ConnectionDied()));
}

Client::~Client()
{
    this->disconnect();
    _tcpSocket->close();
    _tcpSocket->disconnect();
}

QString Client::Name()
{
    return _tcpSocket->peerAddress ().toString();
}

void Client::HandleIncomingPacket()
{
    while(1)
    {
        if(!_receivedHeader)
        {
            int bytesAvailable = _tcpSocket->bytesAvailable();
            if (bytesAvailable < (int)(Message::HeaderSize()))
                return;
            _tcpSocket->read((char*)_rxHeader->RawBuffer(), Message::HeaderSize());

            _rxHeader->SwapHeader();
            _receivedHeader = true;
        }
        if(_receivedHeader)
        {
            int len = _rxHeader->GetTotalLength();
            if (_tcpSocket->bytesAvailable() < len)
            {
                //#qDebug() << "  Client " <<  tcpSocket->peerAddress().toString()+QString(":%1").arg(tcpSocket->peerPort()) << " Waiting for " << tempRxHeader.Length << " bytes, only have " << tcpSocket->bytesAvailable() << endl;
                return;
            }
            QSharedPointer<Message> msg (Message::New(len));
            msg->CopyHdr(*_rxHeader);
            int bytesReadFromSocket = _tcpSocket->read((char*)msg->GetDataPtr(), len);
            if(len != bytesReadFromSocket)
                qDebug() << "len (" << len << " != bytesReadFromSocket(" << bytesReadFromSocket << endl;
            _receivedHeader = false;

            //#qDebug() << "  Client " <<  tcpSocket->peerAddress().toString()+QString(":%1").arg(tcpSocket->peerPort()) << " Sending " << tempRxHeader.Length << " byte message ("
            //#         << tempRxHeader.InterfaceID << "/" << tempRxHeader.MessageID << ")." << endl;

            msg->SwapHeader();
            emit MsgSignal(msg);
        }
    }
}

void Client::MessageSlot(QSharedPointer<Message> msg)
{
    Message* swappedHdr = Message::New(0);
    swappedHdr->CopyHdr(*msg);
    swappedHdr->SwapHeader();
    _tcpSocket->write((const char*)msg->RawBuffer(), Message::HeaderSize());
    int len = swappedHdr->GetTotalLength();
    _tcpSocket->write((const char*)msg->GetDataPtr(), len);
    delete swappedHdr;
}

#if 1 //def REFLECTION_OF_ENUMS_WORKS
#define ENUM_NAME(o,e,v) (o::staticMetaObject.enumerator(o::staticMetaObject.indexOfEnumerator(#e)).valueToKey((v)))
#else
extern QString SocketStateString(QAbstractSocket::SocketState socketState);
#define ENUM_NAME(o,e,v) (SocketStateString(v))
#endif

void Client::SocketStateChanged(QAbstractSocket::SocketState socketState)
{
    qDebug() << "<<<< " << _tcpSocket->peerAddress().toString() << QString(":%1").arg(_tcpSocket->peerPort())
             << ", state changed to " << ENUM_NAME(QAbstractSocket, SocketState, socketState) << endl;
}
