PARSER:=python3 MsgParser.py

install all:: Makefile C Cpp Matlab Python Simulink VHDL

.PHONY: all C Cpp Matlab Python Simulink VHDL test

colorecho  = @printf "\033[0;32m====> Generating $(1)\033[0m\n"

C:
	$(call colorecho,C structures)
	$(TRACE_FLAG)$(PARSER) ../headers obj/C Cpp/language.py  Cpp/CTemplate.h

Cpp:
	$(call colorecho,C++ Code)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Cpp Cpp/language.py  Cpp/CppTemplate.h

Python:
	$(call colorecho,Python)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Python Python/language.py  Python/HeaderTemplate.py
	$(call colorecho,Python)
	$(TRACE_FLAG)$(PARSER) ../messages obj/Python Python/language.py  Python/Template.py

Matlab:
	$(call colorecho,Matlab)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Matlab Matlab/language.py  Matlab/Template.m
	
Simulink:
	$(call colorecho,Simulink)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Matlab Matlab/language.py  Simulink/Template.s
	
VHDL:
	$(call colorecho,VHDL)
	$(TRACE_FLAG)$(PARSER) ../headers obj/VHDL VHDL/language.py  VHDL/Template.vhdl
	
clean clobber::
	rm -rf obj

testCpp:
	python3 test/TestCpp.py

testPython:
	python3 test/TestPython.py

test: testCpp testPython

include ../makefile.inc
