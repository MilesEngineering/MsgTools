include(../../mk/qtcommon.pri)

include($$MSGTOOLSROOT/ThirdParty/qextserialport/src/qextserialport.pri)

TARGET = SerialPlugin
TEMPLATE = lib
CONFIG += plugin

SOURCES +=  \
    SerialPlugin.cpp \
    SerialConnection.cpp
HEADERS += \
    SerialPlugin.h \
    SerialConnection.h \
    ../ServerPort.h \
    ../Message.h \
    ../ServerInterface.h \
    SerialMessage.h

QT += network xml widgets core gui

MY_TARGET = $$TARGET
MY_TARGET = $$replace(MY_TARGET, ^lib, ).plugin
COPY_TARGET = $(COPY_FILE) $(TARGET) ../$$MY_TARGET ; $(COPY_FILE) release/$(TARGET) ../release/$$MY_TARGET ; echo Ignoring results of copy commands, only one of the 2 succeeds
QMAKE_POST_LINK = $$COPY_TARGET
