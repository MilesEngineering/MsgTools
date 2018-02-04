#define UNDEFINED_MSGID (-1)

#include "MsgApp/FieldInfo.h"
#include "MsgApp/MsgInfo.h"
#include "MsgApp/MessageClient.h"
#include "MsgApp/Reflection.h"
#define ENABLE_REFLECTION
#include "Cpp/Network/Connect.h"
#include "Cpp/TestCase1.h"
#include "Cpp/TestCase2.h"
#include "Cpp/TestCase3.h"
#include "C/TestCase1.h"
#include "C/TestCase2.h"
#include "C/TestCase3.h"

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
    cmTx->hdr.SetSource(0x1234);
    cmTx->hdr.SetDestination(0x5678);
    cmTx->hdr.SetPriority(1234);
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
        EXPECT_EQ(cm->hdr.GetDataLength(), (unsigned)ConnectMessage::MSG_SIZE);
        EXPECT_EQ(cm->hdr.GetSource(), cmTx->hdr.GetSource());
        EXPECT_EQ(cm->hdr.GetDestination(), cmTx->hdr.GetDestination());
        EXPECT_EQ(cm->hdr.GetID(), cmTx->hdr.GetID());
        EXPECT_EQ(cm->hdr.GetPriority(), cmTx->hdr.GetPriority());
        /* Verify body */
        EXPECT_STREQ((char*)cm->Name(), (char*)cmTx->Name());
    }

    ConnectMessage* cm = new ConnectMessage();
    MsgInfo* connectMsgInfo = Reflection::FindMsgByID(ConnectMessage::MSG_ID);
    EXPECT_TRUE(connectMsgInfo != NULL);
    if(connectMsgInfo)
    {
        EXPECT_STREQ(connectMsgInfo->Name().toUtf8().constData(), "Connect");
        auto const msgId = ConnectMessage::MSG_ID;
        EXPECT_EQ(connectMsgInfo->ID(), msgId);
    }
    strcpy((char*)cm->Name(), "test1");
    const FieldInfo* fi = connectMsgInfo->GetField("Name");
    EXPECT_TRUE(fi != NULL);
    if(fi)
    {
        QString v = fi->Value(cm->GetDataPtr());
        EXPECT_STREQ(v.toUtf8().constData(), "test1");
    }

    MsgInfo* maMsgInfo = Reflection::FindMsgByID(TestCase1Message::MSG_ID);
    EXPECT_TRUE(maMsgInfo != NULL);
    if(maMsgInfo)
    {
        EXPECT_STREQ(maMsgInfo->Name().toUtf8().constData(), "TestCase1");
        EXPECT_EQ(maMsgInfo->ID(), (unsigned)TestCase1Message::MSG_ID);
    }
    /** \todo Add tests for setting/getting fields of TestCase1, using regular accessors as well as reflection */
}

#define SET(type, field, offset) (type::field##FieldInfo::min + (type::field##FieldInfo::max-type::field##FieldInfo::min)/offset)
#define STEPS 10

TEST(MessageClientTest, CppAndC)
{
    TestCase2Message tc2;
    for(int offset=0; offset<STEPS; offset++)
    {
        SET(TestCase2Message, F1, offset);
        for(int i=0; i<TestCase2Message::F2FieldInfo::count; i++)
            SET(TestCase2Message, F2, STEPS-offset);
        SET(TestCase2Message, F3, offset);
        SET(TestCase2Message, F4, STEPS-offset);
        SET(TestCase2Message, Field5, offset);
        SET(TestCase2Message, Field6, STEPS-offset);

        EXPECT_EQ(unsigned(tc2.GetF1()), TestCase2_GetF1(tc2.GetDataPtr()));
        for(int i=0; i<TestCase2Message::F2FieldInfo::count; i++)
            EXPECT_EQ(tc2.GetF2(i), TestCase2_GetF2(tc2.GetDataPtr(), i));
        EXPECT_EQ(tc2.GetF3(), TestCase2_GetF3(tc2.GetDataPtr()));
        EXPECT_EQ(tc2.GetF4(), TestCase2_GetF4(tc2.GetDataPtr()));
        EXPECT_EQ(tc2.GetField5(), TestCase2_GetField5(tc2.GetDataPtr()));
        EXPECT_EQ(unsigned(tc2.GetField6()), TestCase2_GetField6(tc2.GetDataPtr()));
    }

    TestCase1Message tc1;
    for(int offset=0; offset<STEPS; offset++)
    {
        SET(TestCase1Message, FieldA, offset);
        SET(TestCase1Message, FABitsA, offset);
        SET(TestCase1Message, FieldB, offset);
        EXPECT_EQ(tc1.GetFieldA(), TestCase1_GetFieldA(tc1.GetDataPtr()));
        EXPECT_EQ(tc1.GetFABitsA(), TestCase1_GetFABitsA(tc1.GetDataPtr()));
        EXPECT_EQ(tc1.GetFieldB(), TestCase1_GetFieldB(tc1.GetDataPtr()));
    }
}

int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    ::testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
