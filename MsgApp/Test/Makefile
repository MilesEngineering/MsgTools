.PHONY: all obj

# need to generate code before building app
all :: obj

# run code generator on test case yaml file
PARSER:=python3 ../../CodeGenerator/MsgParser.py
obj :
	$(TRACE_FLAG)$(PARSER) ../../CodeGenerator/test obj/Cpp ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h

TARGET = TestMsgApp

include ../makefile.inc
include $(MK_DIR)/qt.mk


test ::
	../obj/$(TARGET)/release/TestMsgApp

clean clobber::
	rm -rf obj
