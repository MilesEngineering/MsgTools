include ../makefile.inc

ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

all :: WebConsole.html

WebConsole.html: MakeHtml.py
	$(PYTHON) ./MakeHtml.py $@ ../../obj/CodeGenerator/Javascript

clean::
	rm -f WebConsole.html
