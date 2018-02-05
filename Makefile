SUBDIRS := ThirdParty msgtools MsgApp WebConsole

include makefile.inc
include $(MK_DIR)/subdir.mk

bundle:
	rm -f dist/msgtools-*.tar.gz
	python setup.py sdist

testupload:
	twine upload -r test dist/msgtools-*.tar.gz

upload:
	twine upload -r pypi dist/msgtools-*.tar.gz

develop:
	python3 setup.py develop --user

undevelop:
	python3 setup.py develop --user --uninstall
	rm $(HOME)/.local/bin/msg*

android:
	cd AndroidServer && make
