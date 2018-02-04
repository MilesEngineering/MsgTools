ifeq ($(UNAME),Cygwin)

QT_ROOT_57_WIN := /cygdrive/c/Qt/5.7/mingw53_32
QT_ROOT_58_WIN := /cygdrive/c/Qt/Qt5.8.0/5.8/mingw53_32

ifeq ("$(wildcard $(QTROOT_58_WIN))","")

# for Qt 5.8 installed by windows Qt installer, with mingw compiler
QT_ROOT := $(QT_ROOT_58_WIN)
QMAKE := $(QT_ROOT)/bin/qmake.exe
QTBIN := /cygdrive/c/Qt/Qt5.8.0/Tools/mingw530_32/bin
MAKE_FOR_QT = PATH=$(QTBIN):/usr/bin ; mingw32-make

else ifeq ("$(wildcard $(QTROOT_57_WIN))","")

# for Qt 5.7 installed by windows Qt installer, with mingw compiler
QT_ROOT := $(QT_ROOT_57_WIN)
QMAKE := $(QT_ROOT)/bin/qmake.exe
QTBIN := /cygdrive/c/Qt/Tools/mingw530_32/bin
MAKE_FOR_QT = PATH=$(QTBIN):/usr/bin ; mingw32-make

else ifeq ("$(wildcard /usr/bin/qmake)","")

# for qt in path
QMAKE := qmake-qt5
MAKE_FOR_QT := make

endif

# for some reason Qt builds the binary properly, but running it fails because it can't find DLLs.
# it works if you run it from QtCreator, though.
# Extensive googling reveals that this behavior is expected, and the solution is to either:
# 1) copy DLLs to the location the binary is in manually 
# 2) copy DLLs to the location the binary is in using windeployqt.exe
# 3) manually modify the system path
run: $(TARGET)
	PATH=$(QT_ROOT)/bin/ ; $(OBJ_DIR)/release/$(TARGET).exe

else

QMAKE := qmake
MAKE_FOR_QT := make
QSPEC := -spec  linux-g++

endif

ifeq ($(UNAME),Cygwin)
$(OBJ_DIR)/Makefile: *.pro | $(OBJ_DIR)
	@echo Building `cygpath -w $@`
	cd $(OBJ_DIR) ; $(QMAKE) `cygpath -w $(SRCDIR)/$(TARGET).pro`
else
$(OBJ_DIR)/Makefile: *.pro | $(OBJ_DIR)
	@echo Building $@
	cd $(OBJ_DIR) ; $(QMAKE) $(QSPEC) $(SRCDIR)/$(TARGET).pro
endif

$(TARGET) : $(TARGET).pro $(OBJ_DIR)/Makefile
	@echo Building $@
	cd $(OBJ_DIR) ; $(MAKE_FOR_QT)

clean ::
	rm -rf $(OBJ_DIR)

clobber ::
	rm -rf $(OBJ_DIR)
	rm -rf ../build-$(TARGET)*-Qt_*
	rm -f *.pro.user

.PRECIOUS: $(OBJ_DIR)/Makefile

all :: $(TARGET)