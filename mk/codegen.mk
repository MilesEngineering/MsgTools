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
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Python $(CG_DIR)python/language.py  $(CG_DIR)python/Template.py $(CG_DIR)python/HeaderTemplate.py

cpp:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Cpp $(CG_DIR)cpp/language.py  $(CG_DIR)cpp/Template.h $(CG_DIR)cpp/HeaderTemplate.h

c:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/C $(CG_DIR)c/language.py  $(CG_DIR)c/Template.h $(CG_DIR)c/HeaderTemplate.h

java:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Java $(CG_DIR)java/language.py  $(CG_DIR)java/Template.java $(CG_DIR)java/HeaderTemplate.java

js:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Javascript $(CG_DIR)javascript/language.py  $(CG_DIR)javascript/Template.js $(CG_DIR)javascript/HeaderTemplate.js

swift:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Swift $(CG_DIR)swift/language.py  $(CG_DIR)swift/Template.swift $(CG_DIR)swift/HeaderTemplate.swift

matlab:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Matlab/+Messages $(CG_DIR)matlab/language.py  $(CG_DIR)matlab/Template.m $(CG_DIR)matlab/HeaderTemplate.m

html:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Html $(CG_DIR)html/language.py  $(CG_DIR)html/Template.html $(CG_DIR)html/HeaderTemplate.html
	@find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)html/bootstrap.min.css

check: $(DIGEST)

install all:: Makefile check cpp c python java js swift matlab html

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES)) $(CG_DIR)check.py
	$(call colorecho,Checking message validity)
	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)
