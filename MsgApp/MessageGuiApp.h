#include <QtCore>
#include <QtGui>
#include <QMainWindow>

#include "./MessageClient.h"

class MessageGuiApp : public QMainWindow
{
    Q_OBJECT

public:
    MessageGuiApp(const char* name);
    virtual ~MessageGuiApp();

    void connectedToNetwork();
    virtual void newMessageReceived(Message* msg)=0;
private:
    MessageClient* _msgClient;
    const char* _name;

    // GUI ELEMENTS:
    // connection menu item
    // status bar
    // settings persistence
};


