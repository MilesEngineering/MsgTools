include ../makefile.inc

PARSER=python3 MsgParser.py
CHECK=python3 MsgCheck.py
DIGEST=$(MSGDIR)/MsgDigest.txt

.PHONY: all test

mdir:=../messages

MSG_FILES := $(shell cd $(mdir) && find . -iname \*.yaml -printf '%P\n')

CPP_MSG_FILES := $(addprefix $(MSGDIR)/Cpp/,$(MSG_FILES:.yaml=.h))
PYTHON_MSG_FILES := $(addprefix $(MSGDIR)/Python/,$(MSG_FILES:.yaml=.py))
HTML_MSG_FILES := $(addprefix $(MSGDIR)/Html/,$(MSG_FILES:.yaml=.html))

install all:: Makefile $(DIGEST) $(CPP_MSG_FILES) $(PYTHON_MSG_FILES) $(HTML_MSG_FILES)

$(MSGDIR)/Cpp/headers/%.h : $(mdir)/headers/%.yaml Cpp/language.py  Cpp/CppHeaderTemplate.h MsgParser.py Makefile
	$(PARSER) $< $@ Cpp/language.py  Cpp/CppHeaderTemplate.h

$(MSGDIR)/Cpp/%.h : $(mdir)/%.yaml Cpp/language.py  Cpp/CppTemplate.h MsgParser.py Makefile
	$(PARSER) $< $@ Cpp/language.py  Cpp/CppTemplate.h

$(MSGDIR)/Python/headers/%.py : $(mdir)/headers/%.yaml Python/language.py  Python/HeaderTemplate.py MsgParser.py Makefile
	$(PARSER) $< $@ Python/language.py  Python/HeaderTemplate.py

$(MSGDIR)/Python/%.py : $(mdir)/%.yaml Python/language.py  Python/Template.py MsgParser.py Makefile
	$(PARSER) $< $@ Python/language.py  Python/Template.py

$(MSGDIR)/Html/headers/%.html : $(mdir)/headers/%.yaml HTML/language.py  HTML/HeaderTemplate.html MsgParser.py Makefile
	$(PARSER) $< $@ HTML/language.py  HTML/HeaderTemplate.html

$(MSGDIR)/Html/bootstrap.min.css :
	cp HTML/bootstrap.min.css $@

$(MSGDIR)/Html/%.html : $(mdir)/%.yaml HTML/language.py  HTML/Template.html MsgParser.py Makefile $(MSGDIR)/Html/bootstrap.min.css
	$(PARSER) $< $@ HTML/language.py  HTML/Template.html

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

