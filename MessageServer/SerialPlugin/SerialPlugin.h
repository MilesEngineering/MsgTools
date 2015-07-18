#ifndef SERIAL_PLUGIN_H__
#define SERIAL_PLUGIN_H__

#include <QtCore/QObject>
#include <QtCore/qplugin.h>

#include "MessageServer/ServerInterface.h"
#include "SerialConnection.h"

class SerialPlugin : public QObject, public ServerInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "com.milesengineering.msgtools.MessageServerInterface/1.0")
    Q_INTERFACES(ServerInterface)
    public:
        SerialPlugin();
        ServerPort& DBConnection();
    private:
        SerialConnection* serialConn;
};

#endif
