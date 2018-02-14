all:

test: | gmock-1.6.0/obj/libgtest.a gmock-1.6.0/obj/libgmock.a

gmock-1.6.0/obj/libgtest.a gmock-1.6.0/obj/libgmock.a:
ifeq ($(UNAME),Darwin)
	cd gmock-1.6.0 ; CPPFLAGS=-DGTEST_USE_OWN_TR1_TUPLE=1 make -f MsgTools.mk
else
	cd gmock-1.6.0 ; make -f MsgTools.mk
endif

clobber:
	rm -f gmock-1.6.0/obj/*

all clean install :
