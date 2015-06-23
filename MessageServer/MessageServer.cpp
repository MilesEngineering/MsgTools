#include <QtWidgets/QGroupBox>
#include <QtWidgets/QFileDialog>
#include <QList>
#include <QtNetwork>

#include <stdlib.h>

#include "MessageServer.h"
#include "Client.h"
#include "ServerInterface.h"

MessageServer::MessageServer(int /*argc*/, char */*argv*/[])
: QMainWindow(),
  _logFile(0),
  _settings("SPA", "MessageServer")
{
    _tcpServer = new QTcpServer(this);
    if (!_tcpServer->listen(QHostAddress::Any, 5678))
    {
        qDebug() << "Unable to start the server: " << _tcpServer->errorString() << endl;
        exit(1);
        return;
    }

    qDebug() << "The server is running on port " << _tcpServer->serverPort() << endl;

    connect(_tcpServer, SIGNAL(newConnection()), this, SLOT(GotANewClient()));

    _layout = new QVBoxLayout();
    _statusBox = new QPlainTextEdit();
    _statusBox->setMaximumBlockCount(10000);
    _layout->addWidget(_statusBox);

    QGroupBox* box = new QGroupBox;
    box->setLayout(_layout);
    setCentralWidget(box);

    _logButton = new QPushButton("Start Logging");
    connect(_logButton, SIGNAL(clicked()), this, SLOT(LogButton()));
    _layout->addWidget(_logButton);

    _loadPluginButton = new QPushButton("Load Plugin");
    connect(_loadPluginButton, SIGNAL(clicked()), this, SLOT(LoadPluginButton()));
    _layout->addWidget(_loadPluginButton);
}
void MessageServer::LogButton()
{
    if(_logFile)
    {
        _logFile->close();
        _logFile.clear();
        _logButton->setText("Start Logging");
    }
    else
    {
        QString logFileName =
            QFileDialog::getSaveFileName
            (this, tr("Save File"),
             _settings.value("logging/filename", "").toString(),
             tr("Log Files (*.log)"));
        // if they hit cancel, don't do anything
        if(logFileName.isNull())
            return;
        _settings.setValue("logging/filename", logFileName);
        _logFile = QSharedPointer<QFile>(new QFile(logFileName));
        _logFile->open(QIODevice::Append);
        _logButton->setText(QString("Stop %1").arg(logFileName));
    }
}

void MessageServer::LoadPluginButton()
{
    QString pluginFileName =
        QFileDialog::getOpenFileName
        (this, tr("Open Plugin"),
         _settings.value("plugin/filename", "").toString(),
         tr("Plugin Files (*.plugin)"));
    // if they hit cancel, don't do anything
    if(pluginFileName.isNull())
        return;
    _settings.setValue("plugin/filename", pluginFileName);
    LoadPlugin(pluginFileName);
}

void MessageServer::MessageSlot(QSharedPointer<Message> msg)
{
    if(_logFile)
    {
        _logFile->write((const char*)msg->RawBuffer(), Message::HeaderSize());
        _logFile->write((const char*)msg->GetDataPtr(), msg->GetTotalLength());
    }
}

void MessageServer::AddNewClient(ServerPort* serverPort)
{
    qDebug() << "New connection " << serverPort->Name() << endl;
    qDebug() << ">>> connecting new client to clients ";
    // connect the new client to all the existing clients
    for(int i=0; i<_clients.count(); i++)
    {
        connect(serverPort,        SIGNAL(MsgSignal(QSharedPointer<Message>)), _clients.at(i), SLOT(MessageSlot(QSharedPointer<Message>)));
        connect(_clients.at(i), SIGNAL(MsgSignal(QSharedPointer<Message>)), serverPort,        SLOT(MessageSlot(QSharedPointer<Message>)));
        qDebug() << i << ", ";
    }
    qDebug() << " <<<" << endl;

    // add the new client to the list
    _clients.append(serverPort);
    connect(serverPort, SIGNAL(MsgSignal(QSharedPointer<Message>)), this, SLOT(MessageSlot(QSharedPointer<Message>)));
    _layout->addWidget(&serverPort->removeClient);

    connect(serverPort, SIGNAL(disconnected()), this, SLOT(ClientDied()));
}

void MessageServer::GotANewClient()
{
    QTcpSocket *clientSocket = _tcpServer->nextPendingConnection();
    Client* clientConnection = new Client(clientSocket);

    AddNewClient(clientConnection);
}

// remove dead clients from the list of clients
void MessageServer::ClientDied()
{
    ServerPort* dbConn = qobject_cast<ServerPort*>(sender());
    if(_clients.removeOne(dbConn))
        qDebug() << ">>>> Removed client." << endl;
    else
        qDebug() << ">>>> ERROR: Failed to remove client." << endl;
    _layout->removeWidget(&dbConn->removeClient);
    delete dbConn;
}

void MessageServer::LoadPlugin(QString fileName)
{
    // resolve the correct file name for libraries on the given platform
    QLibrary lib(fileName);
    if(!lib.load())
    {
        //qDebug() << "Can't load plugin file: " << lib.fileName()
        //     << endl << "loader reported ";
        qDebug() << lib.errorString() << endl;
        return;
    }
    fileName = lib.fileName();

    QPluginLoader loader(fileName);
    QObject *plugin = loader.instance();

    if (plugin)
    {
            ServerInterface* dbPlugin = qobject_cast<ServerInterface*>(plugin);
            if (dbPlugin)
            {
                ServerPort& dbConn = dbPlugin->DBConnection();
                AddNewClient(&dbConn);
            }
            else
            {
                qDebug() << fileName << " is not a ServerInterface" << endl;
            }
    }
    else
    {
        qDebug() << fileName << " cannot be loaded by QPluginLoader (" << loader.errorString() << endl;
    }
}
