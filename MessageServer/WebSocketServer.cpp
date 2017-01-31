#include "WebSocketServer.h"
#include <QtCore/QDebug>

QT_USE_NAMESPACE

WebSocketServer::WebSocketServer(uint16_t port, QObject *parent)
: QObject(parent),
  webSocketServer(new QWebSocketServer("MsgServer", QWebSocketServer::NonSecureMode, this))
{
    if (webSocketServer->listen(QHostAddress::Any, port))
    {
        //qDebug() << "WebSocketServer listening on port" << port;
        connect(webSocketServer, &QWebSocketServer::newConnection, this, &WebSocketServer::onNewConnection);
    }
}

WebSocketServer::~WebSocketServer()
{
    webSocketServer->close();
}

void WebSocketServer::onNewConnection()
{
    QWebSocket *pSocket = webSocketServer->nextPendingConnection();

    WebSocketClient* wsc = new WebSocketClient(pSocket);

    connect(pSocket, &QWebSocket::binaryMessageReceived, wsc, &WebSocketClient::processBinaryMessage);
    connect(pSocket, &QWebSocket::disconnected, wsc, &WebSocketClient::disconnected);

    emit NewClient(wsc);
}

WebSocketClient::WebSocketClient(QWebSocket* s)
: ServerPort("Websocket"),
  webSocket(s)
{

}

WebSocketClient::~WebSocketClient()
{
    webSocket->deleteLater();
}

void WebSocketClient::processBinaryMessage(QByteArray message)
{
    QSharedPointer<Message> msg (Message::New(message.size()));

    memcpy(msg->RawBuffer(), message.data(), Message::HeaderSize());
    memcpy(msg->GetDataPtr(), &message.data()[Message::HeaderSize()], message.size()-Message::HeaderSize());

    HandleClientMessage(msg);
    emit MsgSignal(msg);
}

void WebSocketClient::MessageSlot(QSharedPointer<Message> msg)
{
    QByteArray ba;
    ba.resize(Message::HeaderSize()+msg->GetDataLength());
    memcpy(ba.data(), msg->RawBuffer(), Message::HeaderSize());
    memcpy(&ba.data()[Message::HeaderSize()], msg->GetDataPtr(), msg->GetDataLength());
    webSocket->sendBinaryMessage(ba);
}

QWidget* WebSocketClient::widget(int index)
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
