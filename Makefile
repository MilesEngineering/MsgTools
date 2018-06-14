SUBDIRS := ThirdParty msgtools MsgApp WebConsole

include makefile.inc
include $(MK_DIR)/subdir.mk

ifeq ($(UNAME),Cygwin)
PYTHON=python.exe
else
PYTHON=python3
endif

bundle:
	rm -f dist/msgtools-*.tar.gz
	$(PYTHON) setup.py sdist

testupload:
	twine upload -r test dist/msgtools-*.tar.gz

upload:
	twine upload -r pypi dist/msgtools-*.tar.gz

develop:
	$(PYTHON) setup.py develop --user

undevelop:
	$(PYTHON) setup.py develop --user --uninstall
	rm $(HOME)/.local/bin/msg*

android:
	cd AndroidServer && make
