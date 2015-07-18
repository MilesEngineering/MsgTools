#include "SerialPlugin.h"

SerialPlugin::SerialPlugin()
: ServerInterface()
{
    serialConn = new SerialConnection();
}

ServerPort& SerialPlugin::DBConnection()
{
    return *serialConn;
}
