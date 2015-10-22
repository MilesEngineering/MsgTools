#ifndef SERVER_INTERFACE_H__
#define SERVER_INTERFACE_H__

#include "ServerPort.h"

class ServerInterface
{
    public:
        virtual ServerPort* CreateConnection()=0;
};

Q_DECLARE_INTERFACE(ServerInterface, "com.milesengineering.msgtools.MessageServerInterface/1.0");

#endif
