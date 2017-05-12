ifneq (3.81,$(firstword $(sort $(MAKE_VERSION) 3.81)))
    $(info ERROR!  You have make version $(MAKE_VERSION))
    $(info We require make version 3.81 or newer.  Please install a newer version of make.)
    $(error Exiting)
endif

THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
MSGTOOLSROOT := $(realpath $(dir $(THIS_MAKEFILE)))
BUILDROOT := $(realpath $(MSGTOOLSROOT)/..)
MK_DIR = $(MSGTOOLSROOT)/mk
MSGDIR = $(BUILDROOT)/obj/CodeGenerator

include $(MK_DIR)/include.mk
