MK_DIR=../mk
include $(MK_DIR)/subdir.mk

SUBDIRS := gccCortexM

# don't connect stlink to top-level build, it's not needed for building, only for debugging
#all :: stlink
debug :: stlink

# if fails on usb, you may need to "sudo apt-get install libusb-1.0-0-dev"
stlink:
	mkdir stlink
	git clone https://github.com/texane/stlink/
	cd stlink; ./autogen.sh; ./configure; make #; sudo make install

