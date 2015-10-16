PARSER=$(TRACE_FLAG)python3 MsgParser.py

install all:: Makefile MsgCheck Cpp Python Html

.PHONY: all Cpp Python test Html MsgCheck

hdir := ../messages/headers
mdir := ../messages

colorecho  = @printf "\033[0;32m====> Generating $(1)\033[0m\n"

Cpp:
	$(call colorecho,C++ Code)
	$(PARSER) $(hdir) $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppHeaderTemplate.h
	$(PARSER) $(mdir) $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppTemplate.h

Python:
	$(call colorecho,Python)
	$(PARSER) $(hdir) $(MSGDIR)/Python Python/language.py  Python/HeaderTemplate.py
	$(PARSER) $(mdir) $(MSGDIR)/Python Python/language.py  Python/Template.py

Html:
	$(call colorecho,HTML)
	$(PARSER) $(hdir) $(MSGDIR)/HTML HTML/language.py  HTML/HeaderTemplate.html
	$(PARSER) $(mdir) $(MSGDIR)/HTML HTML/language.py  HTML/Template.html

MsgCheck:
	$(call colorecho,Checking message validity)
	$(PARSER) $(mdir) $(MSGDIR)/MsgCheck MsgCheck/language.py  MsgCheck/Template.check

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
