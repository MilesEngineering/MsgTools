# recursive make in SUBDIRS
all clean clobber install test ::
	@for dir in _dummy_ $(SUBDIRS); do\
		if [ "$$dir" = "_dummy_" ]; then\
			continue ;\
		fi;\
		if [ ! -d "$$dir" ]; then\
			printf "\033[0;31m==> $(abspath $(CURDIR)/$$dir) does not exist!\033[0m\n"; \
			continue ;\
		fi;\
		if [ ! -e "$$dir/Makefile" ]; then\
			printf "\033[0;31m==> $(abspath $(CURDIR)/$$dir)/Makefile does not exist!\033[0m\n"; \
			continue ;\
		fi;\
		printf "\033[0;32m==> make $(CURDIR)/$$dir \033[0m\n"; \
		"$(MAKE)" -C $$dir --no-print-directory $(MFLAGS) $@ || exit;\
	done
	@printf "\n"
