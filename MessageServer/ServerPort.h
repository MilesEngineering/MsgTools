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
            connect(&removeClient, SIGNAL(clicked()), this, SLOT(ConnectionDied()));
        }
        QString Name() { return name; }
        QPushButton removeClient;
        QString name;
    public slots:
        virtual void MessageSlot(QSharedPointer<Message> msg)=0;
        void ConnectionDied()
        {
            emit disconnected();
        }
    signals:
        void MsgSignal(QSharedPointer<Message> msg);
        void disconnected();
};

#endif
