influx_install:
	sudo apt-get update && sudo apt-get install influxdb

influx_start:
	sudo service influxdb start
	sudo service chronograf start

influx_stop:
	sudo service influxdb stop
	sudo service chronograf stop

# pipe to cat so it exits instead of waiting for user to type 'q'
influx_status:
	service influxdb status | cat
	@echo "\n"
	service chronograf status | cat

influx_version:
	influxd version
	dpkg -l influxdb

QUEST_DB_VERSION := 9.0.3
QUESTDB_DIR := $(HOME)/.local/questdb-$(QUEST_DB_VERSION)-rt-linux-x86-64
QUESTDB_TARBALL := questdb-$(QUEST_DB_VERSION)-rt-linux-x86-64.tar.gz

questdb_install:
	wget https://github.com/questdb/questdb/releases/download/$(QUEST_DB_VERSION)/$(QUESTDB_TARBALL)  -P ~/Downloads
	tar -xvf ~/Downloads/$(QUESTDB_TARBALL) -C ~/.local/

questdb_start:
	$(QUESTDB_DIR)/bin/questdb.sh start

questdb_stop:
	$(QUESTDB_DIR)/bin/questdb.sh stop

# pipe to cat so it exits instead of waiting for user to type 'q'
questdb_status:
	$(QUESTDB_DIR)/bin/questdb.sh status

questdb_version:
	echo $(QUESTDB_DIR)
