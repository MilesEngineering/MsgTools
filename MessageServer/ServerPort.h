#ifndef SERVER_PORT_H__
#define SERVER_PORT_H__

#include <QObject>
#include "Message.h"
#include <QSharedPointer>
#include <QtWidgets/QPushButton>

class ServerPort : public QObject
{
    Q_OBJECT
    public:
        ServerPort(QString n)
        : removeClient(),
          name(n)
        {
            removeClient.setText(QString("Remove ") + Name());
            connect(&removeClient, &QPushButton::clicked, this, &ServerPort::ConnectionDied);
        }
        QString Name() { return name; }
        virtual void MessageSlot(QSharedPointer<Message> msg)=0;
        void ConnectionDied()
        {
            emit disconnected();
        }
        QWidget* widget() { return &removeClient; }
    signals:
        void MsgSignal(QSharedPointer<Message> msg);
        void disconnected();
    private:
        QPushButton removeClient;
        QString name;
};

#endif
