PARSER:=python MsgParser.py

install all:: Makefile C Cpp Matlab Python Simulink VHDL

.PHONY: all C Cpp Matlab Python Simulink VHDL test

colorecho  = @printf "\033[0;32m====> Generating $(1)\033[0m\n"

C:
	$(call colorecho,C structures)
	$(TRACE_FLAG)$(PARSER) ../headers obj/C Cpp/Language.pm  Cpp/CTemplate.h

Cpp:
	$(call colorecho,C++ Code)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Cpp Cpp/Language.pm  Cpp/CppTemplate.h

Python:
	$(call colorecho,Python)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Python Python/Language.pm  Python/Template.py

Matlab:
	$(call colorecho,Matlab)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Matlab Matlab/Language.pm  Matlab/Template.m
	
Simulink:
	$(call colorecho,Simulink)
	$(TRACE_FLAG)$(PARSER) ../headers obj/Matlab Matlab/Language.pm  Simulink/Template.s
	
VHDL:
	$(call colorecho,VHDL)
	$(TRACE_FLAG)$(PARSER) ../headers obj/VHDL VHDL/Language.pm  VHDL/Template.vhdl
	
clean clobber::
	rm -rf obj

test:
	python test/Test.py

include ../makefile.inc
