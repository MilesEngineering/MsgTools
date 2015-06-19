TARGET = MessageServer

TEMPLATE = app

SOURCES += main.cpp \
    MessageServer.cpp \
    Client.cpp

HEADERS += MessageServer.h \
    Client.h \
    ServerPort.h \
    MessageServer.h \
    Message.h \
    Client.h \
    ServerInterface.h

QT += network xml widgets core gui

INCLUDEPATH = ../CodeGenerator/obj/

include(../mk/qtcommon.pri)
