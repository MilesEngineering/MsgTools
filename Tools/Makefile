all:: gccCortexM

GCC_ARM_VERSION := $(shell arm-none-eabi-gcc --version 2>/dev/null)

TOOLCHAIN_NAME:=gcc-arm-none-eabi-4_9-2015q1

ifeq ($(UNAME),Cygwin)
TOOLCHAIN_FILE_NAME:=$(addsuffix -20150306-win32.zip, $(TOOLCHAIN_NAME))
else
TOOLCHAIN_FILE_NAME:=$(addsuffix -20150306-linux.tar.bz2, $(TOOLCHAIN_NAME))
endif

TOOLCHAIN_URL:=https://launchpad.net/gcc-arm-embedded/4.9/4.9-2015-q1-update/+download/$(TOOLCHAIN_FILE_NAME)

.PHONY: all
.INTERMEDIATE: $(TOOLCHAIN_FILE_NAME)

ifdef GCC_ARM_VERSION

.PHONY: gccCortexM
gccCortexM:
	@echo "Found arm-none-eabi-gcc in PATH, not downloading"

else

gccCortexM: $(TOOLCHAIN_FILE_NAME)
ifeq ($(UNAME),Cygwin)
	unzip $^
else
	tar -xvjf $^
	mv $(TOOLCHAIN_NAME) $@
endif

endif

$(TOOLCHAIN_FILE_NAME):
	wget $(TOOLCHAIN_URL)

# don't connect stlink to top-level build, it's not needed for building, only for debugging
#all :: stlink
debug :: stlink

# if fails on usb, you may need to "sudo apt-get install libusb-1.0-0-dev"
stlink:
	mkdir stlink
	git clone https://github.com/texane/stlink/
	cd stlink; ./autogen.sh; ./configure; make #; sudo make install

# don't do anything for clean/clobber/test
clean clobber test ::
	echo "NOT performing $@ for Tools"
