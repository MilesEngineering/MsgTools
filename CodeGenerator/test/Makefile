include ../../makefile.inc

PARSER:=python3 ../MsgParser.py
CHECK:=python3 ../MsgCheck.py
DIGEST:=$(MSGDIR)/test/TestMsgDigest.txt

.PHONY: all test testCpp testPython testJava

MSG_FILES := $(shell find . -iname \*.yaml -printf '%P\n')

CPP_MSG_FILES := $(addprefix $(MSGDIR)/Cpp/test/,$(MSG_FILES:.yaml=.h))
C_MSG_FILES := $(addprefix $(MSGDIR)/C/test/,$(MSG_FILES:.yaml=.h))
PYTHON_MSG_FILES := $(addprefix $(MSGDIR)/Python/test/,$(MSG_FILES:.yaml=.py))
JAVA_MSG_FILES := $(addprefix $(MSGDIR)/Java/test/,$(MSG_FILES:.yaml=.java))
HTML_MSG_FILES := $(addprefix $(MSGDIR)/Html/test/,$(MSG_FILES:.yaml=.html))

.PHONY: python cpp c java html check

python: $(PYTHON_MSG_FILES)

cpp: $(CPP_MSG_FILES)

c: $(C_MSG_FILES)

java: $(JAVA_MSG_FILES)

html: $(HTML_MSG_FILES)

check: $(DIGEST)

install all:: Makefile check cpp c python java html testCpp testPython testJava

$(MSGDIR)/Cpp/test/%.h : %.yaml ../Cpp/language.py  ../Cpp/CppTemplate.h ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Cpp/language.py  ../Cpp/CppTemplate.h

$(MSGDIR)/C/test/%.h : %.yaml ../Cpp/Clanguage.py  ../Cpp/language.py  ../Cpp/CTemplate.h ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Cpp/Clanguage.py  ../Cpp/CTemplate.h

$(MSGDIR)/Java/test/%.java : %.yaml ../Java/language.py  ../Java/JavaTemplate.java ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Java/language.py  ../Java/JavaTemplate.java

$(MSGDIR)/Python/test/%.py : %.yaml ../Python/language.py  ../Python/Template.py ../MsgParser.py Makefile
	$(PARSER) $< $@ ../Python/language.py  ../Python/Template.py

$(MSGDIR)/Html/test/%.html : %.yaml ../HTML/language.py  ../HTML/Template.html ../MsgParser.py Makefile
	$(PARSER) $< $@ ../HTML/language.py  ../HTML/Template.html
	@if [ ! -f $(dir $@)/bootstrap.min.css ]; then cp ../HTML/bootstrap.min.css $(dir $@); fi; 

$(DIGEST): $(MSG_FILES)
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
