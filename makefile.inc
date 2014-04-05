THIS_MAKEFILE := $(lastword $(MAKEFILE_LIST))
BUILDROOT := $(realpath $(dir $(THIS_MAKEFILE)))
MK_DIR = $(BUILDROOT)/mk

include $(MK_DIR)/include.mk
