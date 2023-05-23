.PHONY: build up down

export TAG_QUEEN=$(shell git describe --always --tags --dirty --abbrev=7)
SPECIFIC_COMPOSE_FILE ?= -f docker-compose.yml

build:
	docker-compose $(SPECIFIC_COMPOSE_FILE) build

up:
	docker-compose $(SPECIFIC_COMPOSE_FILE) up -d

down:
	docker-compose $(SPECIFIC_COMPOSE_FILE) down -v

push:
	docker-compose $(SPECIFIC_COMPOSE_FILE) push
