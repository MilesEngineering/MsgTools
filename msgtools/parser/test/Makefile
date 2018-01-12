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
	cd swift && swift build

swiftmsgs:
	msgparser messages swift/Sources/messages swift  Template.swift HeaderTemplate.swift

clean :: cleanswift

cleanswift:
	rm -rf swift/Sources/messages

include $(MK_DIR)/codegen.mk
