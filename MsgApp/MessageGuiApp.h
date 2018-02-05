#ifndef MESSAGE_GUI_APP_H__
#define MESSAGE_GUI_APP_H__

#include <QtCore>
#include <QtGui>
#include <QtWidgets/QMainWindow>

#include "./MessageClient.h"

class MessageGuiApp : public QMainWindow
{
    Q_OBJECT

public:
    MessageGuiApp(const char* name);
    virtual ~MessageGuiApp();

    void connectedToNetwork();
    virtual void newMessageReceived(Message* msg)=0;
    void sendMessage(Message* msg) { _msgClient->sendMessage(msg); }
    virtual void onConnect() {}
private:
    MessageClient* _msgClient;
    const char* _name;

    // GUI ELEMENTS:
    // connection menu item
    // status bar
    // settings persistence
};

#endif
