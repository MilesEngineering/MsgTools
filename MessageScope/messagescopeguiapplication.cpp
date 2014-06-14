#include "messagescopeguiapplication.h"
#include "ui_messagescopeguiapplication.h"

MessageScopeGuiApplication::MessageScopeGuiApplication(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MessageScopeGuiApplication)
{
    ui->setupUi(this);
}

MessageScopeGuiApplication::~MessageScopeGuiApplication()
{
    delete ui;
}
