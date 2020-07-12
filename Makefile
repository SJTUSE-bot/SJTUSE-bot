
.ONESHELL:
.PHONY: mirai help

all: help

## mirai: Download mirai.
mirai:
	wget http://t.imlxy.net:64724/mirai/MiraiOK/miraiOK_linux_amd64 -O Mirai/miraiOK
	chmod +x Mirai/miraiOK
	cd Mirai
	wget https://github.com/project-mirai/mirai-api-http/releases/download/v1.7.3/mirai-api-http-v1.7.3.jar -O plugins/mirai-api-http-v1.7.3.jar
	./miraiOK

## help: Show this help.
help: Makefile
	@echo Usage: make [command]
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'