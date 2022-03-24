install:
	curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
	source /etc/lsb-release
	echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
	sudo apt-get update && sudo apt-get install influxdb

start:
	sudo service influxdb start
	sudo service chronograf start

stop:
	sudo service influxdb stop
	sudo service chronograf stop

# pipe to cat so it exits instead of waiting for user to type 'q'
status:
	service influxdb status | cat
	@echo "\n"
	service chronograf status | cat

check_version:
	influxd version
	dpkg -l influxdb
