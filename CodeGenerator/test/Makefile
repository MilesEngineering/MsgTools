include ../../makefile.inc

PARSER:=python3 ../MsgParser.py
CHECK:=python3 ../MsgCheck.py
DIGEST:=$(MSGDIR)/test/TestMsgDigest.txt

.PHONY: all test testCpp testPython

MSG_FILES := $(shell find . -iname \*.yaml -printf '%P\n')

CPP_MSG_FILES := $(addprefix $(MSGDIR)/Cpp/test/,$(MSG_FILES:.yaml=.h))
PYTHON_MSG_FILES := $(addprefix $(MSGDIR)/Python/test/,$(MSG_FILES:.yaml=.py))
HTML_MSG_FILES := $(addprefix $(MSGDIR)/Html/test/,$(MSG_FILES:.yaml=.html))

.PHONY: python cpp html check

python: $(PYTHON_MSG_FILES)

cpp: $(CPP_MSG_FILES)

html: $(HTML_MSG_FILES)

check: $(DIGEST)

install all:: Makefile check cpp python html testCpp testPython

$(MSGDIR)/Cpp/test/%.h : %.yaml ../Cpp/language.py  ../Cpp/CppTemplate.h ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Cpp/language.py  ../Cpp/CppTemplate.h

$(MSGDIR)/Python/test/%.py : %.yaml ../Python/language.py  ../Python/Template.py ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Python/language.py  ../Python/Template.py

$(MSGDIR)/Html/test/%.html : %.yaml ../HTML/language.py  ../HTML/Template.html ../MsgParser.py Makefile
	$(PARSER) $< $@ ../HTML/language.py  ../HTML/Template.html

$(DIGEST): $(MSG_FILES)
	$(call colorecho,Checking message validity)
	$(CHECK) $(DIGEST) .

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

testCpp:
	./TestCpp.py

testPython:
	./TestPython.py
