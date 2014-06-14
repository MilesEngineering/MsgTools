#include "./MessageGuiApp.h"

MessageGuiApp:MessageGuiApp(MessageTranslator* msgTranslator)
{
    msgClient = new  MsgClient(new QSocket("127.0.0.1:1234"));
    // msgClient = new MsgClient(new QFile("file.bin"));

    _msgTranslator = msgTranslator;

    connect(msgClient, SIGNAL(newMessageComplete(Message*)), this, SIGNAL(newMessageReceived(Message*)));
}
