SUBDIRS := ThirdParty msgtools MsgApp WebConsole

include makefile.inc
include $(MK_DIR)/subdir.mk

# Set default commands for python and pip
PYTHON:=python3
PIP3_INSTALL:=pip3 install
PIP3_UNINSTALL:=pip3 uninstall -y

ifeq ($(UNAME),Cygwin)
  # For Cygwin, use python.exe instead of python3!
  PYTHON:=python.exe
else ifeq ($(UNAME),Linux)
  # For Ubuntu 24.04LTS, we need --break-system-packages :(
  OS_DESCRIPTION=$(shell lsb_release -d)
  ifneq (,$(findstring 24.04,$(OS_DESCRIPTION)))
    PIP3_INSTALL:=$(PIP3_INSTALL) --break-system-packages
    PIP3_UNINSTALL:=$(PIP3_UNINSTALL) --break-system-packages
  endif
endif

bundle:
	rm -f dist/msgtools-*.tar.gz
	$(PYTHON) setup.py sdist

testupload:
	twine upload -r test dist/msgtools-*.tar.gz

upload:
	twine upload -r pypi dist/msgtools-*.tar.gz

# When not inside a virtual env, add --user option on install.
ifeq ($(VIRTUAL_ENV), )
	PIP3_INSTALL:=$(PIP3_INSTALL) --user
endif

install::
	$(PIP3_INSTALL) --editable .[gui]

uninstall::
	$(PIP3_UNINSTALL) msgtools

android:
	cd AndroidServer && make
