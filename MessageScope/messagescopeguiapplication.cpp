#include "messagescopeguiapplication.h"
#include "ui_messagescopeguiapplication.h"

#include "./MessageTranslator.h"

MessageScopeGuiApplication::MessageScopeGuiApplication(QWidget *parent)
  : MessageGuiApp(new MessageTranslator()),
    ui(new Ui::MessageScopeGuiApplication),
    _rxMessages(true),
    _txMessages(false)
{
    ui->setupUi(this);
}

MessageScopeGuiApplication::~MessageScopeGuiApplication()
{
    delete ui;
}

