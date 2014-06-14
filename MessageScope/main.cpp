#include "messagescopeguiapplication.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MessageScopeGuiApplication w;
    w.show();

    return a.exec();
}
