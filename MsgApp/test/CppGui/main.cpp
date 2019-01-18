#include <QApplication>
#include "GuiTestApp.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    GuiTestApp gui;
    gui.show();

    app.exec();

    return 0;
}
