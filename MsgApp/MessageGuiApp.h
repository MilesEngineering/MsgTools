#include <QtCore>
#include <QtGui>
#include <QMainWindow>

#include "./MessageClient.h"

class MessageTranslator;

class MessageGuiApp : public QMainWindow
{
    Q_OBJECT

private:
    MessageClient* _msgClient;
    MessageTranslator* _msgTranslator;

    // GUI ELEMENTS:
    // connection menu item
    // status bar
    // settings persistence

signals:
    void newMessageReceived(Message* msg);

public:
    MessageGuiApp(MessageTranslator* msgTranslator);

};


