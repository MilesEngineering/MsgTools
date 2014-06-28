# qmake often sets both debug and release, for debug builds.
CONFIG(debug, debug|release) {
    DESTDIR=../obj/$$TARGET/debug
} else {
    DESTDIR=../obj/$$TARGET/release
}

UI_DIR = $$DESTDIR
OBJECTS_DIR = $$DESTDIR
RCC_DIR = $$DESTDIR
MOC_DIR = $$DESTDIR
BUILD_DIR = $$DESTDIR

QMAKE_MAKEFILE = Makefile.qt

CONFIG -= debug_and_release
