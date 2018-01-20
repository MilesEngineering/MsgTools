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

testSwift: swiftmsgs
	cd swiftObj && swift build

swiftmsgs:
	msgparser messages swiftObj/Sources/messages swift  Template.swift HeaderTemplate.swift
	cp ../../../MsgApp/FieldAccess.swift swiftObj/Sources/messages

clean :: cleanswift

cleanswift:
	rm -rf swiftObj/Sources swiftObj/.build

include $(MK_DIR)/codegen.mk
