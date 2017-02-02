include ../../makefile.inc

PARSER:=python3 ../MsgParser.py
CHECK:=python3 ../MsgCheck.py
DIGEST:=$(MSGDIR)/MsgDigest.txt

.PHONY: all test testCpp testPython testJava

mdir:=messages

MSG_FILES := $(shell cd $(mdir) && find . -iname \*.yaml -printf '%P\n')

CPP_MSG_FILES := $(addprefix $(MSGDIR)/Cpp/,$(MSG_FILES:.yaml=.h))
C_MSG_FILES := $(addprefix $(MSGDIR)/C/,$(MSG_FILES:.yaml=.h))
PYTHON_MSG_FILES := $(addprefix $(MSGDIR)/Python/,$(MSG_FILES:.yaml=.py))
JAVA_MSG_FILES := $(addprefix $(MSGDIR)/Java/,$(MSG_FILES:.yaml=.java))
JS_MSG_FILES := $(addprefix $(MSGDIR)/Javascript/,$(MSG_FILES:.yaml=.js))
HTML_MSG_FILES := $(addprefix $(MSGDIR)/Html/,$(MSG_FILES:.yaml=.html))

.PHONY: python cpp c java js matlab html check

python: $(PYTHON_MSG_FILES)

cpp: $(CPP_MSG_FILES)

c: $(C_MSG_FILES)

java: $(JAVA_MSG_FILES)

js: $(JS_MSG_FILES)

html: $(HTML_MSG_FILES)

matlab:
	$(PARSER) $(mdir) $(MSGDIR)/Matlab/+Messages ../Matlab/language.py  ../Matlab/Template.m

check: $(DIGEST)

install all:: Makefile check cpp c python java js matlab html testCpp testPython testJava

$(MSGDIR)/Cpp/headers/%.h : $(mdir)/headers/%.yaml ../Cpp/language.py  ../Cpp/CppHeaderTemplate.h ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Cpp/language.py  ../Cpp/CppHeaderTemplate.h

$(MSGDIR)/Cpp/%.h : $(mdir)/%.yaml ../Cpp/language.py  ../Cpp/CppTemplate.h ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Cpp/language.py  ../Cpp/CppTemplate.h

$(MSGDIR)/C/%.h : messages/%.yaml ../Cpp/Clanguage.py  ../Cpp/language.py  ../Cpp/CTemplate.h ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Cpp/Clanguage.py  ../Cpp/CTemplate.h

$(MSGDIR)/Java/%.java : messages/%.yaml ../Java/language.py  ../Java/JavaTemplate.java ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Java/language.py  ../Java/JavaTemplate.java

$(MSGDIR)/Javascript/%.js : messages/%.yaml ../Javascript/language.py  ../Javascript/Template.js ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Javascript/language.py  ../Javascript/Template.js

$(MSGDIR)/Javascript/headers/%.js : messages/headers/%.yaml ../Javascript/language.py  ../Javascript/HeaderTemplate.js ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Javascript/language.py  ../Javascript/HeaderTemplate.js

$(MSGDIR)/Python/%.py : messages/%.yaml ../Python/language.py  ../Python/Template.py ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Python/language.py  ../Python/Template.py

$(MSGDIR)/Python/headers/%.py : $(mdir)/headers/%.yaml ../Python/language.py  ../Python/HeaderTemplate.py ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../Python/language.py  ../Python/HeaderTemplate.py

$(MSGDIR)/Html/%.html : messages/%.yaml ../HTML/language.py  ../HTML/Template.html ../MsgParser.py ../MsgUtils.py Makefile
	$(PARSER) $< $@ ../HTML/language.py  ../HTML/Template.html
	@if [ ! -f $(dir $@)/bootstrap.min.css ]; then cp ../HTML/bootstrap.min.css $(dir $@); fi; 

$(DIGEST): $(addprefix messages/,$(MSG_FILES))
	$(call colorecho,Checking message validity)
	$(CHECK) $(DIGEST) .

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

testCpp:
	./TestCpp.py

testPython:
	./TestPython.py

testJava:
	./TestJava.py
