#ifndef MESSAGE_SERVER_H
#define MESSAGE_SERVER_H

#include <QObject>
#include <QPointer>
#include <QFile>
#include <QTextStream>
#include <QSettings>

#include <QtWidgets/QMainWindow>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QPlainTextEdit>

class QTcpServer;
class ServerPort;

#include "Message.h"

class MessageServer : public QMainWindow
{
    Q_OBJECT

    public:
        static MessageServer* Instance(int argc =0, char** argv = 0);

    private:
        MessageServer(int argc, char *argv[]);

        void GotANewClient();
        void AddNewClient(ServerPort* serverPort);

        void LoadPlugin(QString fileName);
        void LoadPluginButton();

        void LogButtonClicked();
        void MessageSlot(QSharedPointer<Message> msg);

        void ClientDied();
    private:
        QPlainTextEdit*  _statusBox;
        QGridLayout* _layout;
        QPushButton* _logButton;
        QPushButton* _loadPluginButton;
        QSharedPointer<QFile> _logFile;
        QTcpServer* _tcpServer;
        QList<ServerPort*> _clients;
        QSettings _settings;
    private:
        static void redirectDebugOutput(QtMsgType type, const QMessageLogContext &context, const QString &msg);
};

#endif
