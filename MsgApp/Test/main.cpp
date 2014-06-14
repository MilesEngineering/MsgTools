#include "../MessageClient.h"
#include "../../CodeGenerator/obj/Cpp/Connect.h"

#include <iostream>
#include <string>
#include <stdio.h>

#include <gtest/gtest.h>

using namespace std;

#include <QCoreApplication>
#include <QBuffer>

TEST(MessageClientTest, PushButton)
{
    QBuffer buffer;
    MessageClient mc(buffer);

    ConnectMessage cm;
    mc.sendMessage(cm);
    EXPECT_TRUE(1);
    EXPECT_TRUE(0);
}


int main(int argc, char *argv[])
{
    QCoreApplication app(argc, argv);

    ::testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
