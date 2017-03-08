include ../../makefile.inc

.PHONY: testCpp testPython testJava

mdir:=messages

CG_DIR := ../

install all:: testCpp testPython testJava

testCpp:
	./TestCpp.py

testPython:
	./TestPython.py

testJava:
	./TestJava.py

include $(MK_DIR)/codegen.mk

