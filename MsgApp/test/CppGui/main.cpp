#include <QApplication>
#include "MsgApp/FieldInfo.h"
#include "MsgApp/MsgInfo.h"
#include "MsgApp/MessageClient.h"
#include "GuiTestApp.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    GuiTestApp gui;
    gui.show();

    app.exec();

    return 0;
}
