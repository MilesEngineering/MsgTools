#include <QtGui>
#include <QtWidgets/QApplication>
#include "MessageServer.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    MessageServer* server = new MessageServer(argc, argv);
    server->show();
    return app.exec();
}
