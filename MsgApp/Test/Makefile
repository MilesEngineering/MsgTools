include ../makefile.inc

.PHONY: all

pr:
	echo OBJ_DIR  is $(OBJ_DIR)

TARGET = TestMsgApp

include $(MK_DIR)/qt.mk

test :: testCpp testPython

testPython :
	./Test.py

testCpp :
	$(OBJ_DIR)/TestMsgApp

clean clobber::
	rm -rf obj
