#SUBDIRS :=

all:: ChibiOS

OS_NAME:=ChibiOS_2.6.5
OS_FILENAME:=$(OS_NAME).zip
OS_URL:=http://sourceforge.net/projects/chibios/files/ChibiOS_RT%20stable/Version%202.6.5/$(OS_FILENAME)

.PHONY: all
.INTERMEDIATE: $(OS_FILENAME)

ChibiOS: $(OS_FILENAME)
	unzip $(OS_FILENAME)
	mv $(OS_NAME) $@

$(OS_FILENAME):
	wget $(OS_URL)

test::
	@echo $(OS_FILENAME)
	@echo $(OS_NAME)
	@echo $(OS_URL)

MK_DIR=../mk
include $(MK_DIR)/subdir.mk
