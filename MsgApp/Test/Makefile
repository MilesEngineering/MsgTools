include ../makefile.inc

.PHONY: all

# need to generate code before building app
all :: $(OBJ_DIR)/Cpp/TestCase1.h

# run code generator on test case yaml file, put it in our own obj dir, not the main dir for all mesaages in use by all apps.
PARSER=python3 ../../CodeGenerator/MsgParser.py
$(OBJ_DIR)/Cpp/TestCase1.h : ../../CodeGenerator/test/TestCase1.yaml ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h
	$(PARSER) $< $@ ../../CodeGenerator/Cpp/language.py  ../../CodeGenerator/Cpp/CppTemplate.h

TARGET = TestMsgApp

include $(MK_DIR)/qt.mk

test :: testCpp testPython

testPython :
	./Test.py

testCpp :
	$(OBJ_DIR)/TestMsgApp

clean clobber::
	rm -rf obj
