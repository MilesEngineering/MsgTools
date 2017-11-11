ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

PARSER=$(PYTHON) $(CG_DIR)parser.py
CHECK=$(PYTHON) $(CG_DIR)check.py
DIGEST=$(MSGDIR)/MsgDigest.txt

.PHONY: all test

MSG_FILES := $(shell cd $(mdir) && find * -iname \*.yaml)

.PHONY: python cpp c java js swift matlab html check

python:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Python python  Template.py HeaderTemplate.py

cpp:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Cpp cpp  Template.h HeaderTemplate.h

c:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/C c  Template.h HeaderTemplate.h

java:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Java java  Template.java HeaderTemplate.java

js:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Javascript javascript  Template.js HeaderTemplate.js

swift:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Swift swift  Template.swift HeaderTemplate.swift

matlab:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Matlab/+Messages matlab  Template.m HeaderTemplate.m

html:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Html html  Template.html HeaderTemplate.html
	@find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)html/bootstrap.min.css

check: $(DIGEST)

install all:: Makefile check cpp c python java js swift matlab html

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES)) $(CG_DIR)check.py
	$(call colorecho,Checking message validity)
	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)
