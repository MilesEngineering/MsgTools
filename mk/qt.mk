
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

Makefile.qt: *.pro | ../obj/$(TARGET)/debug ../obj/$(TARGET)/release
	@echo Building $@
	$(QMAKE) -spec $(QSPEC) *.pro

$(TARGET) : $(TARGET).pro Makefile.qt
	@echo Building $@
	$(MAKE_FOR_QT) -f Makefile.qt

../obj/$(TARGET)/debug:
	mkdir -p $@

../obj/$(TARGET)/release:
	mkdir -p $@

clean ::
	rm -f Makefile.qt
	rm -rf ../obj/$(TARGET)

clobber ::
	rm -f Makefile.qt
	rm -rf ../obj/$(TARGET)

.PRECIOUS: Makefile.qt

all :: $(TARGET)
