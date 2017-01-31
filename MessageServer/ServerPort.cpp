#include "ServerPort.h"
#include "Cpp/Network/Connect.h"
#include "Cpp/Network/SubscriptionList.h"
#include "Cpp/Network/MaskedSubscription.h"

void ServerPort::HandleClientMessage(QSharedPointer<Message> msg)
{
    uint32_t id = msg->GetMessageID();
    if(id == ConnectMessage::MSG_ID)
    {
        ConnectMessage* connectMsg = (ConnectMessage*)msg.data();
        char name[ConnectMessage::MSG_SIZE];
        for(unsigned i=0; i<sizeof(name); i++)
        {
            name[i] = connectMsg->GetName(i);
        }
        name[sizeof(name)-1] = '\0';
        SetName(name);
    }
    else if(id == MaskedSubscriptionMessage::MSG_ID)
    {
        MaskedSubscriptionMessage* subMsg = (MaskedSubscriptionMessage*)msg.data();
        subscriptionMask = subMsg->GetMask();
        subscriptionValue = subMsg->GetValue();
    }
    else if(id == SubscriptionListMessage::MSG_ID)
    {
        SubscriptionListMessage* subMsg = (SubscriptionListMessage*)msg.data();
        for(int i=0;i<SubscriptionListMessage::IDsFieldInfo::count; i++)
        {
            uint32_t id = subMsg->GetIDs(i);
            subscriptions[id] = true;
        }
    }
}
