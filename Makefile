# Building commands
build:
	docker-compose build

rebuild:
	docker-compose build --no-cache

up:
	docker-compose up -d
down:
	docker-compose down

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
