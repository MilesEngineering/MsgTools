THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MSGTOOLSROOT := $(realpath $(dir $(THIS_MAKEFILE)))
BUILDROOT := $(realpath $(MSGTOOLSROOT)/..)
MK_DIR = $(MSGTOOLSROOT)/mk
MSGDIR = $(BUILDROOT)/obj/CodeGenerator

include $(MK_DIR)/include.mk
