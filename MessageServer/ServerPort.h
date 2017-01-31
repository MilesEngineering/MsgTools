#ifndef SERVER_PORT_H__
#define SERVER_PORT_H__

#include <QObject>
#include "Message.h"
#include <QSharedPointer>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QLabel>
#include <QHash>

class ServerPort : public QObject
{
    Q_OBJECT
    public:
        ServerPort(QString n)
        : removeClient(),
          name(n),
          statusLabel(),
          initName(n),
          subscriptions(),
          subscriptionMask(~0),
          subscriptionValue(0)
        {
            removeClient.setText(QString("Remove"));
            statusLabel.setText(name);
            connect(&removeClient, &QPushButton::clicked, this, &ServerPort::ConnectionDied);
        }
        virtual ~ServerPort() {}
        QString Name() { return name; }
        void SetName(const QString& n) { name = n; statusLabel.setText(name + "(" + initName + ")");}
        virtual void MessageSlot(QSharedPointer<Message> msg)=0;
        void ConnectionDied()
        {
            emit disconnected();
        }
        virtual QWidget* widget(int index)=0;
    signals:
        void MsgSignal(QSharedPointer<Message> msg);
        void disconnected();
    protected:
        QPushButton removeClient;
        QString name;
        QLabel statusLabel;
        QString initName;
        QHash<uint32_t, bool> subscriptions;
        uint32_t subscriptionMask;
        uint32_t subscriptionValue;
        // this handles messages received from our own client connection
        void HandleClientMessage(QSharedPointer<Message> msg);
};

#endif
