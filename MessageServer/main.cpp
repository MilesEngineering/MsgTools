#include <QtGui>
#include <QtWidgets/QApplication>
#include "MessageServer.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    MessageServer* server = MessageServer::Instance(argc, argv);
    server->show();
    server->resize(500,500);
    return app.exec();
}
