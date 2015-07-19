#include <QtCore>
#include <QtGui>
#include <QMainWindow>

#include "./MessageClient.h"

class MessageGuiApp : public QMainWindow
{
    Q_OBJECT

public:
    MessageGuiApp();
    virtual ~MessageGuiApp();

private:
    MessageClient* _msgClient;

    // GUI ELEMENTS:
    // connection menu item
    // status bar
    // settings persistence

signals:
    void newMessageReceived(Message* msg);
};


