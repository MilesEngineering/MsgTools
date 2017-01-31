#ifndef WEBSOCKETSERVER_H
#define WEBSOCKETSERVER_H

#include <QtCore/QObject>
#include <QtCore/QByteArray>

#include <QtWebSockets/QWebSocketServer.h>
#include <QtWebSockets/QWebSocket.h>

#include "ServerPort.h"

class WebSocketClient : public ServerPort
{
    Q_OBJECT
public:
    WebSocketClient(QWebSocket* s);
    virtual ~WebSocketClient();
    QWidget* widget(int index) override;
public slots:
    virtual void MessageSlot(QSharedPointer<Message> msg);
    void processBinaryMessage(QByteArray message);
private:
    QWebSocket* webSocket;
};

class WebSocketServer : public QObject
{
    Q_OBJECT
public:
    WebSocketServer(uint16_t port, QObject* parent = 0);
    virtual ~WebSocketServer();

signals:
    void NewClient(ServerPort* client);

public:
    void onNewConnection();
    void socketDisconnected();

private:
    QWebSocketServer *webSocketServer;
};

#endif // WEBSOCKETSERVER_H
