include ../../makefile.inc

.PHONY: testCpp testPython testJava testKotlin

mdir:=messages

CG_DIR := ../

install all:: testCpp testPython testJava testKotlin

testCpp:
	$(PYTHON) TestCpp.py

testPython:
	$(PYTHON) TestPython.py

testJava:
	$(PYTHON) TestJava.py

testSwift: swiftmsgs
	cd swiftObj && swift build

testKotlin:
	$(PYTHON) TestKotlin.py

swiftmsgs:
	msgparser messages swiftObj/Sources/messages swift  Template.swift HeaderTemplate.swift
	cp ../../../MsgApp/FieldAccess.swift swiftObj/Sources/messages

clean :: cleanswift

cleanswift:
	rm -rf swiftObj/Sources swiftObj/.build

include $(MK_DIR)/codegen.mk
