include ../makefile.inc

.PHONY: all

pr:
	echo OBJ_DIR  is $(OBJ_DIR)

TARGET = TestMsgApp

include $(MK_DIR)/qt.mk

test :: testCpp

testCpp :
	$(OBJ_DIR)/TestMsgApp

clean clobber::
	rm -rf $(OBJ_DIR)
