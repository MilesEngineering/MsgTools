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

.PHONY: python cpp c cosmos java js swift kotlin matlab html check

python:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Python python

cpp:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Cpp cpp

cosmos:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Cosmos cosmos

c:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/C c

$(MSGDIR)/Dart/pubspec.yaml:
	@mkdir -p $(@D)
	echo 'name: messages\ndescription: Auto-generated Dart code from MsgTools, based on YAML message definitions.' > $@

dart: | $(MSGDIR)/Dart/pubspec.yaml
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Dart/lib dart

dartlint:
	cd $(MSGDIR)/Dart ; flutter analyze > lint.txt

java:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Java java

js:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Javascript javascript

swift:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Swift swift

kotlin:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Kotlin kotlin

matlab:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Matlab/+Messages matlab

html:
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Html html
	@find $(MSGDIR)/Html -type d -print0 | xargs -n 1 -0 cp $(CG_DIR)html/bootstrap.min.css

check: $(DIGEST)

all:: Makefile check cpp c cosmos dart python java js swift kotlin matlab html

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES)) $(CG_DIR)check.py
	$(call colorecho,Checking message validity)
	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)

remove_timestamps:
	find $(MSGDIR) -type f | xargs sed -i -e 's/    Created.*//'
