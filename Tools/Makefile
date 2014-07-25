all:: gccCortexM

GCC_ARM_VERSION := $(shell arm-none-eabi-gcc --version 2>/dev/null)

TOOLCHAIN_NAME:=gcc-arm-none-eabi-4_8-2014q2

ifeq ($(UNAME),Cygwin)
TOOLCHAIN_FILE_NAME:=$(addsuffix -20140609-win32.zip, $(TOOLCHAIN_NAME))
else
TOOLCHAIN_FILE_NAME:=$(addsuffix -20140609-linux.tar.bz2, $(TOOLCHAIN_NAME))
endif

TOOLCHAIN_URL:=https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q2-update/+download/$(TOOLCHAIN_FILE_NAME)

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
