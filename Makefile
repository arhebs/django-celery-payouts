.PHONY: help up down build migrate makemigrations shell test lint format worker logs clean

# Default to Docker Compose v2; override with `COMPOSE="docker-compose"` if needed.
COMPOSE ?= docker compose

help:
	@echo "Available commands:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make build        - Build Docker images"
	@echo "  make migrate      - Run database migrations"
	@echo "  make makemigrations - Create new database migrations"
	@echo "  make shell        - Open Django shell inside the web container"
	@echo "  make test         - Run tests inside the web container"
	@echo "  make lint         - Run linters (ruff, mypy) inside the web container"
	@echo "  make format       - Format code with ruff inside the web container"
	@echo "  make worker       - Tail Celery worker logs"
	@echo "  make logs         - Tail all service logs"
	@echo "  make clean        - Stop services and remove containers/volumes"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

migrate:
	$(COMPOSE) exec web python manage.py migrate

makemigrations:
	$(COMPOSE) exec web python manage.py makemigrations

shell:
	$(COMPOSE) exec web python manage.py shell

test:
	$(COMPOSE) exec web pytest -v

lint:
	$(COMPOSE) exec web ruff check .
	$(COMPOSE) exec web mypy apps/

format:
	$(COMPOSE) exec web ruff format .
	$(COMPOSE) exec web ruff check --fix .

worker:
	$(COMPOSE) logs -f celery

logs:
	$(COMPOSE) logs -f

clean:
	$(COMPOSE) down -v --remove-orphans
