
ifeq ($(UNAME),Cygwin)

QT_ROOT := c:/qt/qt5.3.0/5.3/msvc2013_64/
QMAKE := $(QT_ROOT)/bin/qmake.exe
MAKE_FOR_QT = PATH=/cygdrive/c/QtSDK/mingw/bin:/usr/bin; MAKE=c:/QtSDK/Madde/bin/make.exe /cygdrive/c/QtSDK/Madde/bin/make.exe
QSPEC := $(QT_ROOT)/mkspecs/win32-msvc2013

else

QMAKE := qmake -qt=qt5
MAKE_FOR_QT := make
QSPEC :=  linux-g++

endif

../obj/$(TARGET)/Makefile: *.pro | ../obj/$(TARGET)
	@echo Building $@
	cd ../obj/$(TARGET) ; $(QMAKE) -spec $(QSPEC) ../../$(TARGET)/$(TARGET).pro

$(TARGET) : $(TARGET).pro ../obj/$(TARGET)/Makefile
	@echo Building $@
	cd ../obj/$(TARGET) ; $(MAKE_FOR_QT)

../obj/$(TARGET):
	mkdir -p $@

clean ::
	rm -rf ../obj/$(TARGET)

clobber ::
	rm -rf ../obj/$(TARGET)
	rm -rf ../build-$(TARGET)*-Qt_*
	rm -f *.pro.user

.PRECIOUS: ../obj/$(TARGET)/Makefile

all :: $(TARGET)
