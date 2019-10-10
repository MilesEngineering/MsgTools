include ../makefile.inc

ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

all :: WebConsole.html GuiDemo.html

WebConsole.html: MakeHtml.py template.html
	$(PYTHON) ./MakeHtml.py $@ template.html ../../obj/CodeGenerator/Javascript

%.html : %.html.template
	$(PYTHON) ./MakeHtml.py $@ $< ../../obj/CodeGenerator/Javascript

clean::
	rm -f WebConsole.html GuiDemo.html
