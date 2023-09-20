# Define the Docker Compose command based on user input
DOCKER_COMPOSE_CMD ?= docker-compose

# Building commands
build:
	$(DOCKER_COMPOSE_CMD) build

rebuild:
	$(DOCKER_COMPOSE_CMD) build --no-cache

up:
	$(DOCKER_COMPOSE_CMD) up -d

down:
	$(DOCKER_COMPOSE_CMD) down

# Linting commands
lint:
	ruff check . --fix

black:
	black .

cleanimports:
	isort .

# Run tests
testprep:
	docker exec -it flight-blender-web-1 python -m pip install --upgrade -r requirements_dev.txt

test: testprep
	docker exec -it flight-blender-web-1 pytest
