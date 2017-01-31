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
        virtual QWidget* widget(int index)
        {
            switch(index)
            {
                case 0:
                    return &removeClient;
                case 1:
                    return &statusLabel;
                default:
                    return 0;
            }
        }
    private:
        void HandleIncomingPacket();
        void SocketStateChanged(QAbstractSocket::SocketState socketState);
        Message*    _rxHeader;
        bool        _receivedHeader;
        QTcpSocket* _tcpSocket;
};
#endif
