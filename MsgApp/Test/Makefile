include ../makefile.inc

.PHONY: all obj

# need to generate code before building app
all :: obj

# run code generator on test case yaml file, put it in our own obj dir, not the main dir for all mesaages in use by all apps.
PARSER=$(TRACE_FLAG)python3 ../../CodeGenerator/MsgParser.py
obj :
	$(call colorecho,Generating C++ Code)
	$(PARSER) ../../CodeGenerator/test $(OBJ_DIR)/Cpp ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h

TARGET = TestMsgApp

include $(MK_DIR)/qt.mk

test :: testCpp testPython

testPython :
	./Test.py

testCpp :
	$(OBJ_DIR)/TestMsgApp

clean clobber::
	rm -rf obj
