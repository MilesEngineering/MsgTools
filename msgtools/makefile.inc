THIS_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))
include $(THIS_DIR)/../makefile.inc
