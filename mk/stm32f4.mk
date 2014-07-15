all :: make_obj proj

###################################################
# might want separate obj dirs for release vs. debug, or for different processors,
# embedded vs. emulation on host PC, etc.
OBJ_DIR = obj

###################################################
# include all generated dependancy files
# '(-' means it ignores them if they don't exist)
-include $(wildcard $(OBJ_DIR)/*.d)

###################################################
# check for a gcc in the path.  if it's there, use it.  else, look for one in a relative directory.
GCC_ARM_VERSION := $(shell arm-none-eabi-gcc --version 2>/dev/null)
ifdef GCC_ARM_VERSION
BIN_DIR=
else
TOOLCHAIN?=launchpad
BIN_DIR=$(BUILDROOT)/Tools/gccCortexM/$(TOOLCHAIN).$(UNAME)/bin/
endif

CC=$(BIN_DIR)arm-none-eabi-gcc
AR=$(BIN_DIR)arm-none-eabi-ar
OBJCOPY=$(BIN_DIR)arm-none-eabi-objcopy

###################################################
CFLAGS  += -g -O2 -Wall 
CFLAGS += -mlittle-endian -mthumb -mcpu=cortex-m4 -mthumb-interwork
CFLAGS += -mfloat-abi=hard -mfpu=fpv4-sp-d16 -fsingle-precision-constant
CFLAGS += -ffreestanding -nostdlib

###################################################
# list of objects we need to build
# remove extension
OBJECTS := $(basename $(SRCS))
# add new extension
OBJECTS := $(addsuffix .o,$(OBJECTS))
# remove any existing path left over from source file name path
OBJECTS:=$(notdir $(OBJECTS))
# add new path, in the objdir
OBJECTS := $(addprefix $(OBJ_DIR)/,$(OBJECTS))

###################################################
ifeq ($(UNAME),Cygwin)
# for some reason the cygwin compiler puts windows paths in the depend file, but make
# wants unix paths.
FIX_PATHS = && /usr/bin/sed 's|C:|/cygdrive/c|ig' $(@:.o=.d.tmp) > $(@:.o=.d)
COMPILE_COMMAND = $(CC) -MD -MP  -MF $(@:.o=.d.tmp) $(CFLAGS) -o "$@" -c `cygpath -m $<` $(FIX_PATHS)
ASSEMBLE_COMMAND = $(CC) $(CFLAGS) -o "$@" -c `cygpath -m $<`
else
COMPILE_COMMAND = $(CC) -MD -MP  -MF $(@:.o=.d) $(CFLAGS) -o "$@" -c $<
ASSEMBLE_COMMAND = $(CC) $(CFLAGS) -o "$@" -c $<
endif


$(OBJ_DIR)/%.o: %.c
	$(TRACE_FLAG)echo "compiling $<";  $(COMPILE_COMMAND)

$(OBJ_DIR)/%.o: %.cpp
	$(TRACE_FLAG)echo "compiling $<";  $(COMPILE_COMMAND) -fno-rtti -fno-exceptions

$(OBJ_DIR)/%.o: %.s
	$(TRACE_FLAG)echo "assembling $<";  $(ASSEMBLE_COMMAND)

###################################################
# for building an entire project
ifdef PROJ_NAME
CFLAGS += -I$(WINBUILDROOT)/stm32/stmlib
CFLAGS += -I$(WINBUILDROOT)/stm32/stmlib/inc 
CFLAGS += -I$(WINBUILDROOT)/stm32/stmlib/inc/core
CFLAGS += -I$(WINBUILDROOT)/stm32/stmlib/inc/peripherals 
LFLAGS += -T$(WINBUILDROOT)/stm32/stmlib/stm32_flash.ld 

PROJ_NAME := $(OBJ_DIR)/$(PROJ_NAME).elf
PROJ_BIN_NAME := $(PROJ_NAME:.elf=.bin)
PROJ_HEX_NAME := $(PROJ_NAME:.elf=.hex)
proj: $(PROJ_HEX_NAME) $(PROJ_BIN_NAME) $(PROJ_NAME)

$(PROJ_HEX_NAME) $(PROJ_BIN_NAME) $(PROJ_NAME): $(OBJECTS)
	$(TRACE_FLAG)echo "linking $(PROJ_NAME)";  $(CC) $(CFLAGS) $^ -o $(PROJ_NAME) $(LFLAGS)
	$(TRACE_FLAG)echo "generating $(PROJ_HEX_NAME)";  $(OBJCOPY) -O ihex $(PROJ_NAME) $(PROJ_HEX_NAME)
	$(TRACE_FLAG)echo "generating $(PROJ_BIN_NAME)";  $(OBJCOPY) -O binary $(PROJ_NAME) $(PROJ_BIN_NAME)

clean ::
	$(TRACE_FLAG)echo "deleting objects and dependancy files"; rm -f $(OBJECTS) $(OBJECTS:.o=.d)
	rm -f $(PROJ_NAME) $(PROJ_BIN_NAME) $(PROJ_HEX_NAME)
endif

###################################################
# for building a library
ifdef LIB_NAME
LIB_NAME:=$(OBJ_DIR)/lib$(LIB_NAME).a
$(LIB_NAME): $(OBJECTS)
	$(TRACE_FLAG)echo "linking $@";  $(CC) -r -nostdlib -Wl,-X -o $@ $^

proj: $(LIB_NAME)

clean ::
	$(TRACE_FLAG)echo "deleting objects and dependancy files"; rm -f $(OBJECTS) $(OBJECTS:.o=.d)
	rm -f $(LIB_NAME)
endif
