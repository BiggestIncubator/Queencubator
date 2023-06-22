.PHONY: build test up down

export REG=$(shell sed -n 1p .env | cut -d '=' -f2)queencubator
export TAG_QUEEN=$(shell git describe --always --tags --dirty --abbrev=7)
SPECIFIC_COMPOSE_FILE ?= -f docker-compose.yaml
OVERRIDE_VOLUMES_FILE ?= -f docker-compose.override.yaml

changebots:
	deployment/./decom-bot.sh && deployment/./addbots.sh
	
build: down
	deployment/./setup.sh && docker build -t ${REG}:${TAG_QUEEN} .

test: down build
	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) $(OVERRIDE_VOLUMES_FILE) up -d

up: down
	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) up -d

down:
	docker-compose $(SPECIFIC_COMPOSE_FILE) down -v

push: down
	docker image push ${REG}:${TAG_QUEEN}
