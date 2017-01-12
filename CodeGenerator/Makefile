include ../makefile.inc

PARSER=python3 MsgParser.py
CHECK=python3 MsgCheck.py
DIGEST=$(MSGDIR)/MsgDigest.txt

.PHONY: all test

mdir:=../messages

MSG_FILES := $(shell cd $(mdir) && find . -iname \*.yaml -printf '%P\n')

CPP_MSG_FILES := $(addprefix $(MSGDIR)/Cpp/,$(MSG_FILES:.yaml=.h))
C_MSG_FILES := $(addprefix $(MSGDIR)/C/,$(MSG_FILES:.yaml=.h))
PYTHON_MSG_FILES := $(addprefix $(MSGDIR)/Python/,$(MSG_FILES:.yaml=.py))
HTML_MSG_FILES := $(addprefix $(MSGDIR)/Html/,$(MSG_FILES:.yaml=.html))
JAVA_MSG_FILES := $(addprefix $(MSGDIR)/Java/,$(MSG_FILES:.yaml=.java))
JS_MSG_FILES := $(addprefix $(MSGDIR)/Javascript/,$(MSG_FILES:.yaml=.js))

.PHONY: python cpp c java js matlab html check

python: $(PYTHON_MSG_FILES)

cpp: $(CPP_MSG_FILES)

c: $(C_MSG_FILES)

java: $(JAVA_MSG_FILES)

js: $(JS_MSG_FILES)

matlab:
	$(PARSER) $(mdir)/headers $(MSGDIR)/Matlab/+Messages/+headers Matlab/language.py  Matlab/HeaderTemplate.m
	$(PARSER) $(mdir) $(MSGDIR)/Matlab/+Messages Matlab/language.py  Matlab/Template.m

html: $(HTML_MSG_FILES)

check: $(DIGEST)

install all:: Makefile check cpp c python java js matlab html

$(MSGDIR)/Cpp/headers/%.h : $(mdir)/headers/%.yaml Cpp/language.py  Cpp/CppHeaderTemplate.h MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Cpp/language.py  Cpp/CppHeaderTemplate.h

$(MSGDIR)/Cpp/%.h : $(mdir)/%.yaml Cpp/language.py  Cpp/CppTemplate.h MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Cpp/language.py  Cpp/CppTemplate.h

$(MSGDIR)/C/%.h : $(mdir)/%.yaml Cpp/Clanguage.py Cpp/language.py  Cpp/CTemplate.h MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Cpp/Clanguage.py  Cpp/CTemplate.h

$(MSGDIR)/Python/headers/%.py : $(mdir)/headers/%.yaml Python/language.py  Python/HeaderTemplate.py MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Python/language.py  Python/HeaderTemplate.py

$(MSGDIR)/Python/%.py : $(mdir)/%.yaml Python/language.py  Python/Template.py MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Python/language.py  Python/Template.py

$(MSGDIR)/Html/headers/%.html : $(mdir)/headers/%.yaml HTML/language.py  HTML/HeaderTemplate.html MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ HTML/language.py  HTML/HeaderTemplate.html
	@if [ ! -f $(dir $@)/bootstrap.min.css ]; then cp HTML/bootstrap.min.css $(dir $@); fi; 

$(MSGDIR)/Html/%.html : $(mdir)/%.yaml HTML/language.py  HTML/Template.html MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ HTML/language.py  HTML/Template.html
	@if [ ! -f $(dir $@)/bootstrap.min.css ]; then cp HTML/bootstrap.min.css $(dir $@); fi; 

$(MSGDIR)/Java/headers/%.java : $(mdir)/headers/%.yaml Java/language.py  Java/JavaHeaderTemplate.java MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Java/language.py  Java/JavaHeaderTemplate.java

$(MSGDIR)/Java/%.java : $(mdir)/%.yaml Java/language.py  Java/JavaTemplate.java MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Java/language.py  Java/JavaTemplate.java

$(MSGDIR)/Javascript/%.js : $(mdir)/%.yaml Javascript/language.py  Javascript/Template.js MsgParser.py MsgUtils.py Makefile
	$(PARSER) $< $@ Javascript/language.py  Javascript/Template.js

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES))
	$(call colorecho,Checking message validity)
	$(CHECK) $(DIGEST) $(mdir)

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

test:
	cd test && make

#generate regression tests?  To aid in refactoring, by using all generated
# code for regression tests, without having to manually write test cases.
# It would also allow new languages to be written 'test driven' by first
# writing an output file by hand, then programming until the 'regression' test
# passes.
# We could have a makefile target ("make saveResults"?) that copies from
# CodeGenerator/obj to CodeGenerator/expected, and then the test rule
# ("make regressionTest") does a diff of the two directories!

