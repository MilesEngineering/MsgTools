#include <QtWidgets/QGroupBox>
#include <QtWidgets/QFileDialog>
#include <QList>
#include <QtNetwork>
#include <qapplication.h>

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

    connect(_tcpServer, &QTcpServer::newConnection, this, &MessageServer::GotANewClient);

    _layout = new QVBoxLayout();
    _statusBox = new QPlainTextEdit();
    _statusBox->setMaximumBlockCount(10000);
    _layout->addWidget(_statusBox);
    
    qInstallMessageHandler(MessageServer::redirectDebugOutput);

    QGroupBox* box = new QGroupBox;
    box->setLayout(_layout);
    setCentralWidget(box);

    _logButton = new QPushButton("Start Logging");
    connect(_logButton, &QPushButton::clicked, this, &MessageServer::LogButtonClicked);
    _layout->addWidget(_logButton);

    _loadPluginButton = new QPushButton("Load Plugin");
    connect(_loadPluginButton, &QPushButton::clicked, this, &MessageServer::LoadPluginButton);
    _layout->addWidget(_loadPluginButton);
}
void MessageServer::LogButtonClicked()
{
    if(_logFile)
    {
        _logFile->close();
        _logFile.clear();
        _logButton->setText("Start Logging");
    }
    else
    {
        QDate d = QDate::currentDate();
        QTime t = QTime::currentTime();
        QString defaultFilename = d.toString("yyyyMMdd") + "-" + t.toString("hhmmss") + ".log";
        QString logFileName =
            QFileDialog::getSaveFileName
            (this, tr("Save File"),
             _settings.value("logging/filename", ".").toString()+"/"+defaultFilename,
             tr("Log Files (*.log)"));
        // if they hit cancel, don't do anything
        if(logFileName.isNull())
            return;
        _logFile = QSharedPointer<QFile>(new QFile(logFileName));
        _logFile->open(QIODevice::Append);
        QFileInfo fileInfo(logFileName);
        _settings.setValue("logging/filename", fileInfo.dir().absolutePath());
        _logButton->setText(QString("Stop %1").arg(fileInfo.fileName()));
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
        connect(serverPort,     &ServerPort::MsgSignal, _clients.at(i), &ServerPort::MessageSlot);
        connect(_clients.at(i), &ServerPort::MsgSignal, serverPort,     &ServerPort::MessageSlot);
        qDebug() << i << ", ";
    }
    qDebug() << " <<<" << endl;

    // add the new client to the list
    _clients.append(serverPort);
    connect(serverPort, &ServerPort::MsgSignal, this, &MessageServer::MessageSlot);
    _layout->addWidget(serverPort->widget());

    connect(serverPort, &ServerPort::disconnected, this, &MessageServer::ClientDied);
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
    _layout->removeWidget(dbConn->widget());
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

void MessageServer::redirectDebugOutput(QtMsgType type, const QMessageLogContext& /*context*/, const QString &msg)
{
    QString output = msg;// + "("+context.file + ":" + context.line + ", " + context.function + ")";
    switch (type)
    {
    case QtDebugMsg:
        Instance()->_statusBox->appendPlainText(output);
        break;
    case QtWarningMsg:
        Instance()->_statusBox->appendPlainText("Warning: " + output);
        break;
    case QtCriticalMsg:
        Instance()->_statusBox->appendPlainText("Critical: " + output);
        break;
    case QtFatalMsg:
        fprintf(stderr, "Fatal: %s", output.toUtf8().constData());
        abort();
    }
}

MessageServer* MessageServer::Instance(int argc, char** argv)
{
    static MessageServer* instance = new MessageServer(argc, argv);
    return instance;
}
