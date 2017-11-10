include ../makefile.inc

mdir := ../../../messages

CG_DIR := 

test:
	cd test && make

include $(MK_DIR)/codegen.mk

#generate regression tests?  To aid in refactoring, by using all generated
# code for regression tests, without having to manually write test cases.
# It would also allow new languages to be written 'test driven' by first
# writing an output file by hand, then programming until the 'regression' test
# passes.
# We could have a makefile target ("make saveResults"?) that copies from
# CodeGenerator/obj to CodeGenerator/expected, and then the test rule
# ("make regressionTest") does a diff of the two directories!

