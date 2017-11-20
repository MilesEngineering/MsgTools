include ../../makefile.inc

.PHONY: testCpp testPython testJava

mdir:=messages

CG_DIR := ../

install all:: testCpp testPython testJava

testCpp:
	$(PYTHON) TestCpp.py

testPython:
	$(PYTHON) TestPython.py

testJava:
	$(PYTHON) TestJava.py

include $(MK_DIR)/codegen.mk

