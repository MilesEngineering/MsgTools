PARSER:=python3 ../../CodeGenerator/MsgParser.py

all ::
	$(TRACE_FLAG)$(PARSER) ../../CodeGenerator/test obj/Cpp ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h

TARGET = TestMsgApp

include ../makefile.inc
include $(MK_DIR)/qt.mk


test ::
	../obj/$(TARGET)/release/TestMsgApp
