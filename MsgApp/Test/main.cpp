#include "MsgApp/MessageClient.h"
#include "MsgApp/FieldInfo.h"
#include "MsgApp/MsgInfo.h"
#include "MsgApp/Reflection.h"
#include "Cpp/Network/Connect.h"
#include "Cpp/TestCase1.h"

#include <iostream>
#include <string>
#include <stdio.h>

#include <gtest/gtest.h>

using namespace std;

#include <QCoreApplication>
#include <QBuffer>
#include <QtTest/QTest>
#include <QtTest/QSignalSpy>

Q_DECLARE_METATYPE(Message*)

TEST(MessageClientTest, Reflection)
{
    qRegisterMetaType<Message*>("Message*");
    QBuffer buffer;
    buffer.open(QIODevice::ReadWrite);
    MessageClient mc(&buffer);

    ConnectMessage* cmTx = new ConnectMessage();
    cmTx->hdr->SetSource(0x1234);
    cmTx->hdr->SetDestination(0x5678);
    cmTx->hdr->SetPriority(1234);
    strcpy((char*)cmTx->Name(), "test1");
    /* Connect the signal so we can receive a message, and test that send/receive works. */
    QSignalSpy* ss = new QSignalSpy(&mc, SIGNAL(newMessageComplete(Message*)));
    EXPECT_TRUE(ss->isValid());
    mc.sendMessage(cmTx);
    /** \todo This is stupid, but read() won't work unless we close/reopen, or seek to start! */
    /** \todo Need to find a better workaround.  We don't want to have the MessageClient::onDataReady()
              seek to zero, because that won't work for files containing messages. */
    buffer.seek(0);
    ss->wait(100);
    // Verify there is one message received */
    EXPECT_EQ(ss->count(), 1);
    if(ss->count() == 1)
    {
        QList<QVariant> arguments = ss->takeFirst();
        Message* cmRx = (Message*)(arguments.at(0).value<Message*>());
        ConnectMessage* cm = (ConnectMessage*)cmRx;
        EXPECT_TRUE(cmRx != 0);
        /* Verify header */
        EXPECT_EQ(cm->hdr->GetLength(), ConnectMessage::MSG_SIZE);
        EXPECT_EQ(cm->hdr->GetSource(), cmTx->hdr->GetSource());
        EXPECT_EQ(cm->hdr->GetDestination(), cmTx->hdr->GetDestination());
        EXPECT_EQ(cm->hdr->GetID(), cmTx->hdr->GetID());
        EXPECT_EQ(cm->hdr->GetPriority(), cmTx->hdr->GetPriority());
        /* Verify body */
        EXPECT_STREQ((char*)cm->Name(), (char*)cmTx->Name());
    }

    ConnectMessage* cm = new ConnectMessage();
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

    /** \todo This is bad!  Need to have the message info get added automatically to reflection! */
    Reflection::AddMsg(MsgAMessage::ReflectionInfo());
    MsgAMessage* mam = new MsgAMessage();
    MsgInfo* maMsgInfo = Reflection::FindMsgByID(mam->MSG_ID);
    EXPECT_TRUE(maMsgInfo != NULL);
    if(maMsgInfo)
    {
        EXPECT_STREQ(maMsgInfo->Name().toUtf8().constData(), "MsgA");
        EXPECT_EQ(maMsgInfo->ID(), mam->MSG_ID);
    }
    /** \todo Add tests for setting/getting fields of MsgA, using regular accessors as well as reflection */
}


int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    ::testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
