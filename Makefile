.PHONY: build up down

REG=$(shell sed -n 1p .env | cut -d '=' -f2)queencubator
export TAG_QUEEN=$(shell git describe --always --tags --dirty --abbrev=7)
SPECIFIC_COMPOSE_FILE ?= -f docker-compose.yaml
OVERRIDE_VOLUMES_FILE ?= -f docker-compose.override.yaml

build:
	docker build -t ${REG}:${TAG_QUEEN} .
#	docker build -t queen:${TAG_QUEEN} .
test: build
	docker-compose $(SPECIFIC_COMPOSE_FILE) $(OVERRIDE_VOLUMES_FILE) up -d

up:
	docker-compose $(SPECIFIC_COMPOSE_FILE) up -d

down:
	docker-compose $(SPECIFIC_COMPOSE_FILE) down -v

push:
	docker-compose $(SPECIFIC_COMPOSE_FILE) push
