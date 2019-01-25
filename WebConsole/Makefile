include ../makefile.inc

ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

all :: WebConsole.html

WebConsole.html: MakeHtml.py
	$(PYTHON) ../msgtools/webapp/webapp.py WebConsole ../obj/CodeGenerator/javascript/ ./
	mkdir -p obj/CodeGenerator
	cp -r ../obj/CodeGenerator/javascript ./obj/CodeGenerator/

clean::
	rm -f WebConsole.html
	rm -r obj
	rm -f index.html
	rm -f *.js
