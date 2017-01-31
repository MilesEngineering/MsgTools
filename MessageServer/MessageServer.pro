include(../mk/qtcommon.pri)

TARGET = MessageServer

TEMPLATE = app

SOURCES += main.cpp \
    MessageServer.cpp \
    Client.cpp \
    WebSocketServer.cpp \
    ServerPort.cpp

HEADERS += MessageServer.h \
    Client.h \
    ServerPort.h \
    ../MsgApp/Message.h \
    ServerInterface.h \
    WebSocketServer.h

QT += network xml widgets core gui websockets
