#ifndef GUI_TEST_APP_H
#define GUI_TEST_APP_H

#include "MsgApp/MessageGuiApp.h"
#include "MsgApp/Reflection.h"

//# For reflection to be enabled, there needs to be one place in your application
//# that defines #ENABLE_REFLECTION, and then #includes all auto-generated headers
//# you want reflection info for.  This should be an auto-generated file!
#define ENABLE_REFLECTION
#include "Cpp/TestCase1.h"
#include "Cpp/TestCase2.h"
#include "Cpp/TestCase3.h"

#include "QTextEdit"

#define spaces(n) QString("%1").arg("", n)

class GuiTestApp : public MessageGuiApp
{
    Q_OBJECT
public:
    GuiTestApp()
    : MessageGuiApp("test client")
    {
        te = new QTextEdit();
        te->setReadOnly(true);
        setCentralWidget(te);
    }

    void newMessageReceived(Message* msg)
    {
        if(msg->GetMessageID() == TestCase1Message::MSG_ID)
        {
            TestCase1Message* tc1 = (TestCase1Message*)msg;
            tc1->GetBitsA();
            te->append("got tc1, sending tc2");
            TestCase2Message tc2;
            tc2.SetF1((TestCase2Message::TestEnum)tc1->GetFieldA());
            tc2.SetF2(tc1->GetFieldB(), 0);
            tc2.SetF3(tc1->GetBitsC());
            tc2.SetF4(tc1->GetFieldD());
            sendMessage(&tc2);
        }
        MsgInfo* msgInfo = Reflection::FindMsgByID(msg->GetMessageID());
        if(msgInfo)
        {
            te->append(Reflection::ToCSV(msg, true));
            QString csv = Reflection::ToCSV(msg);
            te->append(csv);
            te->append(Reflection::ToJSON(msg));

            QSharedPointer<Message> csvTestMsg = Reflection::FromCSV(csv);
            sendMessage(csvTestMsg.data());
#if 0
            int nameLen = msgInfo->Name().length();
            te->append(msgInfo->Name() + ":");
            for(int fieldIndex=0; fieldIndex<msgInfo->GetFields().count();  fieldIndex++)
            {
                FieldInfo* fieldInfo = msgInfo->GetFields()[fieldIndex];
                if(fieldInfo->Count() == 1)
                {
                    te->append(QString("%1.%2 = %3").arg(spaces(nameLen)).arg(fieldInfo->Name()).arg(fieldInfo->Value(msg->GetDataPtr())));
                }
                else
                {
                    te->append(QString("%1.%2[%3]").arg(spaces(nameLen)).arg(fieldInfo->Name()).arg(fieldInfo->Count()));
                    int fieldNameLen = fieldInfo->Name().length();
                    for(int i=0; i<fieldInfo->Count(); i++)
                    {
                        te->append(QString("%1 %2[%3] = %3").arg(spaces(nameLen)).arg(spaces(fieldNameLen)).arg(i).arg(fieldInfo->Value(msg->GetDataPtr())));
                    }
                }
            }
#endif
        }
        else
        {
            te->append(QString("no info for %1").arg(msg->GetMessageID()));
        }
    }
private:
    QTextEdit* te;
};

#endif // GUITESTAPP_H
