#include <QtWidgets/QGroupBox>
#include <QtWidgets/QFileDialog>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QVBoxLayout>
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
  _settings("MsgTools", "MessageServer")
{
    _statusBox = new QPlainTextEdit();
    _statusBox->setMaximumBlockCount(10000);
    qInstallMessageHandler(MessageServer::redirectDebugOutput);

    _tcpServer = new QTcpServer(this);
    if (!_tcpServer->listen(QHostAddress::Any, 5678))
    {
        qWarning() << "Unable to start the server: " << _tcpServer->errorString() << endl;
        exit(1);
        return;
    }

    /** Show IP address and port number in status bar */
    QString name = "";
    foreach (const QHostAddress &address, QNetworkInterface::allAddresses())
    {
        if (address.protocol() == QAbstractSocket::IPv4Protocol &&
            address != QHostAddress(QHostAddress::LocalHost))
        {
            QString addrStr = address.toString();
            // ignore VM/VPN stuff (special ubuntu address, and anything that ends in 1)
            if(addrStr.section( ".",-1,-1 ) != "1" && addrStr != "192.168.122.1")
               name += address.toString() + "/";
        }
    }
    name.remove(-1, 1);
    name += QString(" : %1").arg(_tcpServer->serverPort());
    statusBar()->addPermanentWidget(new QLabel(name));

    connect(_tcpServer, &QTcpServer::newConnection, this, &MessageServer::GotANewClient);

    QVBoxLayout* vbox = new QVBoxLayout();
    _layout = new QGridLayout();
    
    QGroupBox* box = new QGroupBox;
    box->setLayout(vbox);
    setCentralWidget(box);

    _logButton = new QPushButton("Start Logging");
    connect(_logButton, &QPushButton::clicked, this, &MessageServer::LogButtonClicked);
    vbox->addWidget(_logButton);

    _loadPluginButton = new QPushButton("Load Plugin");
    connect(_loadPluginButton, &QPushButton::clicked, this, &MessageServer::LoadPluginButton);
    vbox->addWidget(_loadPluginButton);

    vbox->addLayout(_layout);
    vbox->addWidget(_statusBox);
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
         _settings.value("plugin/filename", QCoreApplication::applicationDirPath()).toString(),
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
        _logFile->write((const char*)msg->GetDataPtr(), msg->GetDataLength());
    }
}

void MessageServer::AddNewClient(ServerPort* serverPort)
{
    // connect the new client to all the existing clients
    for(int i=0; i<_clients.count(); i++)
    {
        connect(serverPort,     &ServerPort::MsgSignal, _clients.at(i), &ServerPort::MessageSlot);
        connect(_clients.at(i), &ServerPort::MsgSignal, serverPort,     &ServerPort::MessageSlot);
    }

    // add the new client to the list
    _clients.append(serverPort);
    connect(serverPort, &ServerPort::MsgSignal, this, &MessageServer::MessageSlot);
    int clientRow = _layout->rowCount();
    for(int i=0; ; i++)
    {
        QWidget* widget = serverPort->widget(i);
        if(!widget)
            break;
        _layout->addWidget(widget, clientRow, i);
    }

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
    QObject* s = QObject::sender();
    /** \note this used to be qobject_cast<>, which failed for an object that was a subclass of
     * ServerPort defined in the SerialPlugin.  Changing to dynamic_cast<> made it work again. */
    ServerPort* serverPort = dynamic_cast<ServerPort*>(s);
    if(serverPort)
    {
        if(_clients.removeOne(serverPort))
        {
            qDebug() << "Removed client " << serverPort->Name() << endl;
            statusBar()->showMessage(QString("Removed %1").arg(serverPort->Name()), 1000);
            for(int i=0; ; i++)
            {
                QWidget* widget = serverPort->widget(i);
                if(!widget)
                    break;
                _layout->removeWidget(widget);
            }
            delete serverPort;
        }
        else
        {
            qCritical() << "Failed to remove client " << endl; // << dbConn->Name() << endl;
        }
    }
    else
    {
        qCritical() << "got ClientDied from sender not a ServerPort " << endl;
    }
}

void MessageServer::LoadPlugin(QString fileName)
{
    // resolve the correct file name for libraries on the given platform
    QLibrary lib(fileName);
    if(!lib.load())
    {
        qWarning() << fileName << " cannot be loaded by QLibrary (" << lib.errorString() << ")" << endl;
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
            ServerPort* conn = dbPlugin->CreateConnection();
            AddNewClient(conn);
        }
        else
        {
            qWarning() << fileName << " is not a ServerInterface" << endl;
        }
    }
    else
    {
        qWarning() << fileName << " cannot be loaded by QPluginLoader (" << loader.errorString() << ")" << endl;
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
    case QtInfoMsg:
        break;
    }
}

MessageServer* MessageServer::Instance(int argc, char** argv)
{
    static MessageServer* instance = new MessageServer(argc, argv);
    return instance;
}
