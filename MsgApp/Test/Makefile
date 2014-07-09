PARSER:=python3 ../../CodeGenerator/MsgParser.py

TARGET = TestMsgApp

include ../makefile.inc
include $(MK_DIR)/qt.mk

test ::
	$(TRACE_FLAG)$(PARSER) ../../CodeGenerator/test obj/Cpp ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h
	../obj/$(TARGET)/release/TestMsgApp
