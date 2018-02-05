all : gtest gmock

###############################################################################
# Google Test (gtest) rules
# Note: these rules are different from the curl or xmlrpc rules because
# gtest make does not support 'make install'.
# In addition, 'make all' makes libgtest.la and libgtest_main.la files,
# not gtest.a and gtest_main.a, which are needed for linking by the individual
# gtest use case files.
# Hence gtest.a and gtest_main.a are generated explicitly here.
.PHONY: gtest gmock clean install

GMOCK_DIR = $(CURDIR)
GTEST_DIR = $(GMOCK_DIR)/gtest

gmock: obj/libgmock.a obj/libgmock_main.a

gtest: obj/libgtest.a obj/libgtest_main.a

# Recipes for building gtest and gmock libraries
# The following is taken straight from $(GTEST_DIR)/make/Makefile.=
# except that the .a files are named libxxx.a so libtool can more
# readily use them.
VPATH := $(GTEST_DIR)/src:$(GMOCK_DIR)/src

obj/%.o : %.cc
	mkdir -p obj
	@echo Compiling $<
	@$(CXX) $(CPPFLAGS) -I$(GTEST_DIR) -I$(GTEST_DIR)/include -I$(GMOCK_DIR) -I$(GMOCK_DIR)/include $(CXXFLAGS) -c $< -o $@

obj/libgtest.a : obj/gtest-all.o
	@$(AR) $(ARFLAGS) $@ $^

obj/libgtest_main.a : obj/gtest-all.o obj/gtest_main.o
	@$(AR) $(ARFLAGS) $@ $^

obj/libgmock.a : obj/gmock-all.o obj/gtest-all.o
	@$(AR) $(ARFLAGS) $@ $^

obj/libgmock_main.a : obj/gmock-all.o obj/gmock_main.o obj/gtest-all.o obj/gtest_main.o
	@$(AR) $(ARFLAGS) $@ $^

clean:
	@rm -f obj/*.a
	@rm -f obj/*.o
	@if [ -d obj ]; then rmdir obj; fi
