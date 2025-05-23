/*
    Created from:
        Messages = <INPUTFILENAME>
        Template = <TEMPLATEFILENAME>
        Language = <LANGUAGEFILENAME>

                     AUTOGENERATED FILE, DO NOT EDIT

*/
#include <memory>
#include "<OUTPUTFILEBASENAME>.h"


#include "message.h"
#include "../Cpp/<OUTPUTFILEBASENAME>.h"
#include "simulink_message_client.h"


void <MSGFULLNAME>Send(const <MSGFULLNAME>Unpacked* unpackedMsg, int src = 0, int dst = 0)
{
    auto msg = std::make_unique<<MSGFULLNAME>Message>();
    msg->m_hdr.SetSource(src);
    msg->m_hdr.SetDestination(dst);
    <SETFIELDS>
    SimulinkMessageClient::Instance()->SendMsg(*msg);
}


void <MSGFULLNAME>Receive(<MSGFULLNAME>Unpacked* unpackedMsg, int src = 0, int dst = 0)
{
    SimulinkMessageClient::Instance()->ReadAllMessages();
    Message *msgbase = SimulinkMessageClient::Instance()->RegisterRxBlock(<MSGFULLNAME>Message::MSG_ID, src, dst);
    if (!msgbase)
    {
        // not clear what to do here, not setting values will 
        // not necessarily leave them holding previous values
    }
    <MSGFULLNAME>Message *msg = reinterpret_cast<<MSGFULLNAME>Message*>(msgbase);
    <GETFIELDS>

    // does msg need to be deleted here?
}
