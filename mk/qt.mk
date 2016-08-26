ifeq ($(UNAME),Cygwin)

# for old version of Qt on windows
#QT_ROOT := c:/qt/qt5.3.0/5.3/msvc2013_64/
#QMAKE := $(QT_ROOT)/bin/qmake.exe
#MAKE_FOR_QT = PATH=/cygdrive/c/QtSDK/mingw/bin:/usr/bin; MAKE=c:/QtSDK/Madde/bin/make.exe /cygdrive/c/QtSDK/Madde/bin/make.exe
#QSPEC := -spec $(QT_ROOT)/mkspecs/win32-msvc2013

#QT_ROOT := c:/Qt/5.7/mingw53_32
#QMAKE := $(QT_ROOT)/bin/qmake.exe
##MAKE_FOR_QT = PATH=/cygdrive/c/QtSDK/mingw/bin:/usr/bin; MAKE=c:/QtSDK/Madde/bin/make.exe /cygdrive/c/QtSDK/Madde/bin/make.exe
#MAKE_FOR_QT = make
#QSPEC := -spec $(QT_ROOT)/mkspecs/win32-g++

# for qt in cygwin
QMAKE := qmake-qt5
MAKE_FOR_QT := make
#QSPEC := -spec linux-g++

else

QMAKE := qmake -qt=qt5
MAKE_FOR_QT := make
QSPEC := -spec  linux-g++

endif

$(OBJ_DIR)/Makefile: *.pro | $(OBJ_DIR)
	@echo Building `cygpath -w $@`
	cd $(OBJ_DIR) ; $(QMAKE) $(QSPEC) `cygpath -w $(SRCDIR)/$(TARGET).pro`

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
