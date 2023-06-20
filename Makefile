.PHONY: build test up down

export REG=$(shell sed -n 1p .env | cut -d '=' -f2)queencubator
export TAG_QUEEN=$(shell git describe --always --tags --dirty --abbrev=7)
SPECIFIC_COMPOSE_FILE ?= -f docker-compose.yaml
OVERRIDE_VOLUMES_FILE ?= -f docker-compose.override.yaml

build:
	deployment/./setup.sh && docker build -t ${REG}:${TAG_QUEEN} . && rm docker-compose.*

test: build
	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) $(OVERRIDE_VOLUMES_FILE) up -d && rm docker-compose.*

up:
	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) up -d && rm docker-compose.*

down:
	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) down -v && rm docker-compose.*

push:
#	deployment/./setup.sh && docker-compose $(SPECIFIC_COMPOSE_FILE) push && rm docker-compose.*
	docker image push ${REG}:${TAG_QUEEN}
