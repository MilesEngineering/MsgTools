#ifndef __CLIENT_CONNECTION_H_
#define __CLIENT_CONNECTION_H_

#include "ServerPort.h"

#include <QtNetwork>
#include <QtNetwork/QTcpSocket>

class Client : public ServerPort
{
    Q_OBJECT
    public:
        Client(QTcpSocket* sock);
        ~Client();
        virtual QString Name();
        void MessageSlot(QSharedPointer<Message> msg) override;
    private:
        void HandleIncomingPacket();
        void SocketStateChanged(QAbstractSocket::SocketState socketState);
        Message*    _rxHeader;
        bool        _receivedHeader;
        QTcpSocket* _tcpSocket;
};
#endif
