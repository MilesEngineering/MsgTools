PARSER=$(TRACE_FLAG)python3 MsgParser.py
CHECK=$(TRACE_FLAG)python3 MsgCheck.py
DIGEST=$(MSGDIR)/MsgDigest.txt

install all:: Makefile MsgCheck Cpp Python Html

.PHONY: all Cpp Python test Html MsgCheck

hdir := ../messages/headers
mdir := ../messages

Cpp:
	$(call colorecho,Generating C++ Code)
	$(PARSER) $(hdir) $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppHeaderTemplate.h
	$(PARSER) $(mdir) $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppTemplate.h

Python:
	$(call colorecho,Generating Python)
	$(PARSER) $(hdir) $(MSGDIR)/Python Python/language.py  Python/HeaderTemplate.py
	$(PARSER) $(mdir) $(MSGDIR)/Python Python/language.py  Python/Template.py

Html:
	$(call colorecho,Generating HTML)
	$(PARSER) $(hdir) $(MSGDIR)/HTML HTML/language.py  HTML/HeaderTemplate.html
	$(PARSER) $(mdir) $(MSGDIR)/HTML HTML/language.py  HTML/Template.html

MsgCheck:
	$(call colorecho,Checking message validity)
	$(CHECK) $(mdir) $(DIGEST)

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

testCpp:
	./test/TestCpp.py

testPython:
	./test/TestPython.py

test: testCpp testPython

#generate regression tests?  To aid in refactoring, by using all generated
# code for regression tests, without having to manually write test cases.
# It would also allow new languages to be written 'test driven' by first
# writing an output file by hand, then programming until the 'regression' test
# passes.
# We could have a makefile target ("make saveResults"?) that copies from
# CodeGenerator/obj to CodeGenerator/expected, and then the test rule
# ("make regressionTest") does a diff of the two directories!

include ../makefile.inc
