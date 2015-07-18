BUILDROOT = $$clean_path($$PWD/..)
MSGDIR = $$BUILDROOT/obj/CodeGenerator
SRCDIR = $$_PRO_FILE_PWD_
OBJDIR = $$BUILDROOT/obj/$$replace(SRCDIR, $$BUILDROOT, )

INCLUDEPATH += $$MSGDIR $$BUILDROOT $$BUILDROOT/MsgApp $$BUILDROOT/ThirdParty

QMAKE_CXXFLAGS += -fno-strict-aliasing -std=c++11
