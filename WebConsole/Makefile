include ../makefile.inc

ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

all :: WebConsole.html

WebConsole.html: MakeHtml.py
	$(PYTHON) ../msgtools/webapp/webapp.py -s WebConsole ../obj/CodeGenerator/javascript/ ./

clean::
	rm -f WebConsole.html
	rm -rf messages
	rm -f index.html
	rm -f *.js
