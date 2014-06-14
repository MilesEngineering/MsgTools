#include <QtCore>
#include <QtGui>

#include "./MessageClient.h"
#include "./MessageTranslator.h"

class MsgGUIApp : QMainWindow
{
    Q_OBJECT

private:
    MessageClient* _msgClient;
    MessageTranslator* _msgTranslator;

    // GUI ELEMENTS:
    // connection menu item
    // status bar
    // settings persistence

protected:
    signal void newMessageReceived(Message* msg);

public:
    MsgGUIApp(MsgTranslator* msgTranslator);

};


