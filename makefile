FLASK_APP_PY := run.py
FLASK_APP := run:app
DOCKER_COMPOSE_FILE := ./ags_deployment/docker-compose-prod.yml
DOCKER_COMPOSE_FILE_LOCAL := ./ags_deployment/docker-compose-dev.yml
DOCKER_SERVICE_NAME := app

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make run-dev-docker        - Run the 「HTTP」 application in development mode with LOCAL Docker Compose"
	@echo "  make run-dev-docker-ngrok  - Run the 「HTTPS」 application in development mode with LOCAL Docker Compose"
	@echo "  make run-prod              - Run the application in PROD mode with GITLAB Docker Compose"


# Run in HTTTP DEV env via LOCAL Docker Compose
.PHONY: run-dev-docker
run-dev-docker:
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) down
	docker image prune -f
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) up --build -d $(DOCKER_SERVICE_NAME)
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) logs -f $(DOCKER_SERVICE_NAME)

# Run in HTTPS DEV env via LOCAL Docker Compose
.PHONY: run-dev-docker-ngrok
run-dev-docker-ngrok:
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) down
	docker image prune -f
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) up --build -d
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) logs -f $(DOCKER_SERVICE_NAME) &
	docker-compose -f $(DOCKER_COMPOSE_FILE_LOCAL) logs -f ngrok

# Run in PROD env via GITLAB Docker Compose
.PHONY: run-prod
run-prod:
	@echo "========== Starting Docker Compose Process =========="
	@echo "========== 1. Stopping and removing containers, and cleaning up unused images =========="
	docker-compose -f $(DOCKER_COMPOSE_FILE) down
	docker image prune -f
	@echo "========== 2. Building and starting the Docker service ($(DOCKER_SERVICE_NAME)) =========="
	docker-compose -f $(DOCKER_COMPOSE_FILE) up --build -d $(DOCKER_SERVICE_NAME)
	@echo "========== 3. Checking the status of the Docker service ($(DOCKER_SERVICE_NAME)) =========="
	docker-compose -f $(DOCKER_COMPOSE_FILE) ps
	@echo "========== Docker Compose Process Complete =========="