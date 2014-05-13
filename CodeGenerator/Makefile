PARSER:=python3 MsgParser.py

install all:: Makefile Cpp Python
#C Matlab Simulink VHDL

.PHONY: all C Cpp Matlab Python Simulink VHDL test

hdir = ../messages/headers

colorecho  = @printf "\033[0;32m====> Generating $(1)\033[0m\n"

C:
	$(call colorecho,C structures)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/C Cpp/language.py  Cpp/CTemplate.h

Cpp:
	$(call colorecho,C++ Code)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/Cpp Cpp/language.py  Cpp/CppTemplate.h

Python:
	$(call colorecho,Python)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/Python Python/language.py  Python/HeaderTemplate.py
	$(TRACE_FLAG)$(PARSER) ../messages obj/Python Python/language.py  Python/Template.py

Matlab:
	$(call colorecho,Matlab)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/Matlab Matlab/language.py  Matlab/Template.m
	
Simulink:
	$(call colorecho,Simulink)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/Matlab Matlab/language.py  Simulink/Template.s
	
VHDL:
	$(call colorecho,VHDL)
	$(TRACE_FLAG)$(PARSER) $(hdir) obj/VHDL VHDL/language.py  VHDL/Template.vhdl
	
clean clobber::
	rm -rf obj

testCpp:
	python3 test/TestCpp.py

testPython:
	python3 test/TestPython.py

test: testCpp testPython

#generate regression tests?  To aid in refactoring, by using all generated code for regression tests, without having to manually write test cases.
# would also allow new languages to be written 'test driven' by first writing an output file by hand, then programming until the 'regression' test passes.
#    could have a makefile target ("make saveResults"?)that copies from CodeGenerator/obj to CodeGenerator/expected,
#    and then the test rule ("make regressionTest") does a diff of the two directories!

include ../makefile.inc
