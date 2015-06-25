#ifndef SERVER_PORT_H__
#define SERVER_PORT_H__

#include <QObject>
#include "Message.h"
#include <QSharedPointer>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QLabel>

class ServerPort : public QObject
{
    Q_OBJECT
    public:
        ServerPort(QString n)
        : removeClient(),
          name(n),
          statusLabel(),
          initName(n)
        {
            removeClient.setText(QString("Remove"));
            statusLabel.setText(name);
            connect(&removeClient, &QPushButton::clicked, this, &ServerPort::ConnectionDied);
        }
        QString Name() { return name; }
        void SetName(const QString& n) { name = n; statusLabel.setText(name + "(" + initName + ")");}
        virtual void MessageSlot(QSharedPointer<Message> msg)=0;
        void ConnectionDied()
        {
            emit disconnected();
        }
        QWidget* widget(int index)
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
    signals:
        void MsgSignal(QSharedPointer<Message> msg);
        void disconnected();
    protected:
        QPushButton removeClient;
        QString name;
        QLabel statusLabel;
        QString initName;
};

#endif
