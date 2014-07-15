CFLAGS += -Iinc

SRCS = stm32f4xx_it.c main.c system_stm32f4xx.c startup_stm32f4xx.s 

LFLAGS += -L$(WINBUILDROOT)/stm32/stmlib/obj -lstm32f4

# all the files will be generated with this name
PROJ_NAME:=blinky

include ../../makefile.inc
include $(MK_DIR)/stm32f4.mk

vpath %.c src
vpath %.s $(BUILDROOT)/stm32/stmlib
