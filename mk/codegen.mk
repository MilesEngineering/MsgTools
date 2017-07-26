debug:
	@echo CG_DIR is $(CG_DIR)

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
	$(PARSER) $(mdir)/headers $(call CYGPATH,$(MSGDIR))/Matlab/+Messages/+headers $(CG_DIR)Matlab/language.py  $(CG_DIR)Matlab/HeaderTemplate.m
	$(PARSER) $(mdir) $(call CYGPATH,$(MSGDIR))/Matlab/+Messages $(CG_DIR)Matlab/language.py  $(CG_DIR)Matlab/Template.m

html: $(HTML_MSG_FILES)

check: $(DIGEST)

install all:: Makefile check cpp c python java js matlab html

$(MSGDIR)/Cpp/headers/%.h : $(mdir)/headers/%.yaml $(CG_DIR)Cpp/language.py  $(CG_DIR)Cpp/CppHeaderTemplate.h $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Cpp/language.py  $(CG_DIR)Cpp/CppHeaderTemplate.h

$(MSGDIR)/Cpp/%.h : $(mdir)/%.yaml $(CG_DIR)Cpp/language.py  $(CG_DIR)Cpp/CppTemplate.h $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Cpp/language.py  $(CG_DIR)Cpp/CppTemplate.h

$(MSGDIR)/C/headers/%.h : $(mdir)/headers/%.yaml $(CG_DIR)Cpp/Clanguage.py  $(CG_DIR)Cpp/language.py $(CG_DIR)Cpp/CHeaderTemplate.h $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Cpp/Clanguage.py  $(CG_DIR)Cpp/CHeaderTemplate.h

$(MSGDIR)/C/%.h : $(mdir)/%.yaml $(CG_DIR)Cpp/Clanguage.py $(CG_DIR)Cpp/language.py $(CG_DIR)Cpp/Clanguage.py  $(CG_DIR)Cpp/CTemplate.h $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Cpp/Clanguage.py  $(CG_DIR)Cpp/CTemplate.h

$(MSGDIR)/Python/headers/%.py : $(mdir)/headers/%.yaml $(CG_DIR)Python/language.py  $(CG_DIR)Python/HeaderTemplate.py $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Python/language.py  $(CG_DIR)Python/HeaderTemplate.py

$(MSGDIR)/Python/%.py : $(mdir)/%.yaml $(CG_DIR)Python/language.py  $(CG_DIR)Python/Template.py $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Python/language.py  $(CG_DIR)Python/Template.py

$(MSGDIR)/Html/headers/%.html : $(mdir)/headers/%.yaml $(CG_DIR)HTML/language.py  $(CG_DIR)HTML/HeaderTemplate.html $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)HTML/language.py  $(CG_DIR)HTML/HeaderTemplate.html
	@if [ ! -f $(call CYGPATH,$(dir $@))/bootstrap.min.css ]; then cp $(CG_DIR)HTML/bootstrap.min.css $(call CYGPATH,$(dir $@)); fi; 

$(MSGDIR)/Html/%.html : $(mdir)/%.yaml $(CG_DIR)HTML/language.py  $(CG_DIR)HTML/Template.html $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)HTML/language.py  $(CG_DIR)HTML/Template.html
	@if [ ! -f $(call CYGPATH,$(dir $@))/bootstrap.min.css ]; then cp $(CG_DIR)HTML/bootstrap.min.css $(call CYGPATH,$(dir $@)); fi; 

$(MSGDIR)/Java/headers/%.java : $(mdir)/headers/%.yaml $(CG_DIR)Java/language.py  $(CG_DIR)Java/JavaHeaderTemplate.java $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Java/language.py  $(CG_DIR)Java/JavaHeaderTemplate.java

$(MSGDIR)/Java/%.java : $(mdir)/%.yaml $(CG_DIR)Java/language.py  $(CG_DIR)Java/JavaTemplate.java $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Java/language.py  $(CG_DIR)Java/JavaTemplate.java

$(MSGDIR)/Javascript/headers/%.js : $(mdir)/headers/%.yaml $(CG_DIR)Javascript/language.py  $(CG_DIR)Javascript/HeaderTemplate.js $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Javascript/language.py  $(CG_DIR)Javascript/HeaderTemplate.js

$(MSGDIR)/Javascript/%.js : $(mdir)/%.yaml $(CG_DIR)Javascript/language.py  $(CG_DIR)Javascript/Template.js $(CG_DIR)MsgParser.py $(CG_DIR)MsgUtils.py Makefile
	$(PARSER) $< $(call CYGPATH,$@) $(CG_DIR)Javascript/language.py  $(CG_DIR)Javascript/Template.js

clean clobber::
	rm -rf $(MSGDIR) __pycache__ *.pyc

$(DIGEST): $(addprefix $(mdir)/,$(MSG_FILES))
	$(call colorecho,Checking message validity)
	$(CHECK) $(call CYGPATH,$(DIGEST)) $(mdir)
