ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

PARSER=$(PYTHON) $(CG_DIR)MsgParser.py
CHECK=$(PYTHON) $(CG_DIR)MsgCheck.py
DIGEST=$(MSGDIR)/MsgDigest.txt

.PHONY: all test

MSG_FILES := $(shell cd $(mdir) && find * -iname \*.yaml)

.PHONY: python cpp c java js matlab html check

python:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Python $(CG_DIR)Python/language.py  $(CG_DIR)Python/Template.py $(CG_DIR)Python/HeaderTemplate.py

cpp:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Cpp $(CG_DIR)Cpp/language.py  $(CG_DIR)Cpp/CppTemplate.h $(CG_DIR)Cpp/CppHeaderTemplate.h

c:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/C $(CG_DIR)Cpp/Clanguage.py  $(CG_DIR)Cpp/CTemplate.h $(CG_DIR)Cpp/CHeaderTemplate.h

java:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Java $(CG_DIR)Java/language.py  $(CG_DIR)Java/JavaTemplate.java $(CG_DIR)Java/JavaHeaderTemplate.java

js:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Javascript $(CG_DIR)Javascript/language.py  $(CG_DIR)Javascript/Template.js $(CG_DIR)Javascript/HeaderTemplate.js

matlab:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Matlab/+Messages $(CG_DIR)Matlab/language.py  $(CG_DIR)Matlab/Template.m $(CG_DIR)Matlab/HeaderTemplate.m

html:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Html $(CG_DIR)HTML/language.py  $(CG_DIR)HTML/Template.html $(CG_DIR)HTML/HeaderTemplate.html
	@find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)HTML/bootstrap.min.css

check: $(DIGEST)

install all:: Makefile check cpp c python java js matlab html

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES)) $(CG_DIR)MsgCheck.py
	$(call colorecho,Checking message validity)
	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)
