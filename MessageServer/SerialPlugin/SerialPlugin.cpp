#include "SerialPlugin.h"

SerialPlugin::SerialPlugin()
: ServerInterface()
{
}

ServerPort* SerialPlugin::CreateConnection()
{
    SerialConnection* serialConn = new SerialConnection();
    return serialConn;
}
