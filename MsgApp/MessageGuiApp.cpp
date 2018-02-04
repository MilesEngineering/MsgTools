#include <QTcpSocket>
#include <QHostAddress>
#include <QSharedPointer>

#include "./MessageGuiApp.h"

#include "Cpp/Network/Connect.h"
#include "Cpp/Network/MaskedSubscription.h"

MessageGuiApp::MessageGuiApp(const char* name)
: QMainWindow(),
  _name(name)
{
    QTcpSocket* s = new QTcpSocket();
    _msgClient = new MessageClient(s);
    connect(_msgClient, &MessageClient::newMessageComplete, this, &MessageGuiApp::newMessageReceived);
    connect(s, &QTcpSocket::connected, this, &MessageGuiApp::connectedToNetwork);

    s->connectToHost(QHostAddress::LocalHost, 5678);
}

MessageGuiApp::~MessageGuiApp()
{
}

void MessageGuiApp::connectedToNetwork()
{
    MaskedSubscriptionMessage s;
    _msgClient->sendMessage(&s);
    ConnectMessage c;
    strncpy((char*)c.Name(), _name, qMin(int(ConnectMessage::MSG_SIZE), int(strlen(_name))));
    _msgClient->sendMessage(&c);

    onConnect();
}
