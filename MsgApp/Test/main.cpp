#include "../MessageClient.h"
#include "../FieldInfo.h"
#include "../MsgInfo.h"
#include "../Reflection.h"
#include "../../CodeGenerator/obj/Cpp/Connect.h"

#include <iostream>
#include <string>
#include <stdio.h>

#include <gtest/gtest.h>

using namespace std;

#include <QCoreApplication>
#include <QBuffer>

TEST(MessageClientTest, Reflection)
{
    QBuffer buffer;
    buffer.open(QIODevice::ReadWrite);
    MessageClient mc(&buffer);

    ConnectMessage* cm = new ConnectMessage();
    mc.sendMessage(cm);
    /** \todo Need to connect the signal so we can receive a message, and test that send/receive works! */
    //connect(&mc, SIGNAL(newMessageComplete(Message*)), this, SLOT(msgComplete(Message*)));

    MsgInfo* connectMsgInfo = Reflection::FindMsgByID(cm->MSG_ID);
    EXPECT_TRUE(connectMsgInfo == NULL);
    /** \todo This is bad!  Need to have the message info get added automatically to reflection! */
    Reflection::AddMsg(ConnectMessage::ReflectionInfo());
    connectMsgInfo = Reflection::FindMsgByID(cm->MSG_ID);
    EXPECT_TRUE(connectMsgInfo != NULL);
    if(connectMsgInfo)
    {
        EXPECT_STREQ(connectMsgInfo->Name().toUtf8().constData(), "Connect");
        EXPECT_EQ(connectMsgInfo->ID(), cm->MSG_ID);
    }
    strcpy((char*)cm->Name(), "test1");
    const FieldInfo* fi = connectMsgInfo->GetField("Name");
    EXPECT_TRUE(fi != NULL);
    if(fi)
    {
        QString v = fi->Value(*cm);
        EXPECT_STREQ(v.toUtf8().constData(), "test1");
    }
}


int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    ::testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
