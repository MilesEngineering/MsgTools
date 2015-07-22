PARSER:=python3 MsgParser.py

install all:: Makefile Cpp Python Html
# Simulink

.PHONY: all C Cpp Matlab Python Simulink VHDL test

hdir = ../messages/headers

colorecho  = @printf "\033[0;32m====> Generating $(1)\033[0m\n"

Cpp:
	$(call colorecho,C++ Code)
	$(TRACE_FLAG)$(PARSER) $(hdir) $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppHeaderTemplate.h
	$(TRACE_FLAG)$(PARSER) ../messages $(MSGDIR)/Cpp Cpp/language.py  Cpp/CppTemplate.h

Python:
	$(call colorecho,Python)
	$(TRACE_FLAG)$(PARSER) $(hdir) $(MSGDIR)/Python Python/language.py  Python/HeaderTemplate.py
	$(TRACE_FLAG)$(PARSER) ../messages $(MSGDIR)/Python Python/language.py  Python/Template.py

Html:
	$(call colorecho,HTML)
	$(TRACE_FLAG)$(PARSER) $(hdir) $(MSGDIR)/HTML HTML/language.py  HTML/HeaderTemplate.html
	$(TRACE_FLAG)$(PARSER) ../messages $(MSGDIR)/HTML HTML/language.py  HTML/Template.html

Simulink:
	$(call colorecho,Simulink)
	$(TRACE_FLAG)$(PARSER) $(hdir) $(MSGDIR)/Matlab Matlab/language.py  Simulink/Template.s
	
clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

testCpp:
	./test/TestCpp.py

testPython:
	./test/TestPython.py

test: testCpp testPython

#generate regression tests?  To aid in refactoring, by using all generated code for regression tests, without having to manually write test cases.
# would also allow new languages to be written 'test driven' by first writing an output file by hand, then programming until the 'regression' test passes.
#    could have a makefile target ("make saveResults"?)that copies from CodeGenerator/obj to CodeGenerator/expected,
#    and then the test rule ("make regressionTest") does a diff of the two directories!

include ../makefile.inc
