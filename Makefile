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

ifeq ($(VIRTUAL_ENV), )
# When not inside a virtual env, use --user option on install,
# and remove the user's invocation scripts on uninstall.
develop:
	pip3 install --editable .[gui] --user

undevelop:
	pip3 uninstall -y msgtools
	rm $(HOME)/.local/bin/msg*
else
# When inside a virtual env, we don't need --user,
# and there's no invocation scripts to remove.
develop:
	pip3 install --editable .[gui]

undevelop:
	pip3 uninstall -y msgtools
endif

android:
	cd AndroidServer && make
