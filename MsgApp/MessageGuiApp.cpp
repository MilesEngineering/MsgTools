#include <QTcpSocket>
#include <QHostAddress>
#include <QSharedPointer>

#include "./MessageGuiApp.h"

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

#define DISABLE_REFLECTION
#include "Cpp/Network/Connect.h"

void MessageGuiApp::connectedToNetwork()
{
    ConnectMessage c;
    strncpy((char*)c.Name(), _name, ConnectMessage::MSG_SIZE);
    _msgClient->sendMessage(&c);
}

MessageGuiApp::~MessageGuiApp()
{
}
