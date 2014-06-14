#ifndef MESSAGESCOPEGUIAPPLICATION_H
#define MESSAGESCOPEGUIAPPLICATION_H

#include <QMainWindow>

#include "./MessageTreeModel.h"

namespace Ui
{
class MessageScopeGuiApplication;
}

class MessageScopeGuiApplication : public MessageGuiApp
{
    Q_OBJECT

public:
    MessageScopeGuiApplication(QWidget *parent = 0);
    ~MessageScopeGuiApplication();

protected:

private:
    Ui::MessageScopeGuiApplication *ui;

    MessageTreeModel _rxMessages;
    MessageTreeModel _txMessages;
};

#endif // MESSAGESCOPEGUIAPPLICATION_H
