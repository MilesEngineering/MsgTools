all clobber clean install :: 

.PHONY: all clobber clean install test

printdirs:
	@echo THIS_MAKEFILE is $(THIS_MAKEFILE)
	@echo BUILDROOT is $(BUILDROOT)
	@echo MK_DIR is $(MK_DIR)

# this is overrideable at the command line like so:
#      TRACE=1 make
TRACE?=0
TRACEON=$(TRACE:0=@)
TRACE_FLAG=$(TRACEON:1=)

# Simplify uname variable for cygwin
UNAME:=$(shell uname)
ifneq (,$(findstring CYGWIN,$(UNAME)))
UNAME:=Cygwin
endif

ifeq ($(UNAME),Cygwin)
WINBUILDROOT:=$(shell cygpath -m $(BUILDROOT))
ESCWINBUILDROOT:=$(subst \,\\,$(WINBUILDROOT))
WINCURDIR:=$(subst /,\\,$(shell cygpath -m $(CURDIR)))
WINCURDIR:=$(subst /,\\,$(WINCURDIR))
else
WINBUILDROOT:=$(BUILDROOT)
ESCWINBUILDROOT:=$(BUILDROOT)
WINCURDIR:=$(CURDIR)
endif

# may need to get more sophisticated in the future, if we build for multiple platforms
OBJ_DIR := obj
make_obj :
	@if [ ! -d "$(OBJ_DIR)" ]; then\
		mkdir -p $(OBJ_DIR);\
	fi
