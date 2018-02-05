MSGTOOLSROOT = $$clean_path($$PWD/..)
BUILDROOT = $$clean_path($$PWD/../..)
MSGTOOLSDIRNAME = $$relative_path($$MSGTOOLSROOT,$$BUILDROOT)
MSGDIR = $$BUILDROOT/obj/CodeGenerator
SRCDIR = $$_PRO_FILE_PWD_
OBJDIR = $$BUILDROOT/obj/$$replace(SRCDIR, $$BUILDROOT, )

INCLUDEPATH += $$MSGDIR $$MSGTOOLSROOT $$MSGTOOLSROOT/MsgApp $$MSGTOOLSROOT/ThirdParty

QMAKE_CXXFLAGS += -fno-strict-aliasing -std=c++11

QT += core gui widgets network
