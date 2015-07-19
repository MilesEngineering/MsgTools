#include <QTcpSocket>

#include "./MessageGuiApp.h"

MessageGuiApp::MessageGuiApp()
 : QMainWindow(),
   _msgClient(new MessageClient(new QTcpSocket()))
{
    connect(_msgClient, SIGNAL(newMessageComplete(Message*)), this, SIGNAL(newMessageReceived(Message*)));
}

MessageGuiApp::~MessageGuiApp()
{
}
