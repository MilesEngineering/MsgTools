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
    public slots:
        void MessageSlot(QSharedPointer<Message> msg) override;
    private slots:
        void HandleIncomingPacket();
        void SocketStateChanged(QAbstractSocket::SocketState socketState);
private:
        Message*    _rxHeader;
        bool        _receivedHeader;
        QTcpSocket* _tcpSocket;
};
#endif
