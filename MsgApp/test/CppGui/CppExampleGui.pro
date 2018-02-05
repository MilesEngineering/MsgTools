#-------------------------------------------------
#
# Project created by QtCreator 2014-06-13T15:11:59
#
#-------------------------------------------------
include(../../../mk/qtcommon.pri)

INCLUDEPATH += .

TARGET = CppExampleGui
TEMPLATE = app

SOURCES += main.cpp\
    ../../MessageGuiApp.cpp

HEADERS  += ../../MessageClient.h \
    $$MSGDIR/Cpp/headers/NetworkHeader.h \
    ../../Message.h \
    ../../FieldInfo.h \
    ../../MsgInfo.h \
    ../../Reflection.h \
    ../../MessageGuiApp.h \
    GuiTestApp.h

INCLUDEPATH += $$OBJDIR
