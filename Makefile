.PHONY: help install test test-fast test-local test-ci test-ci-fast lint format format-check security db-up migrate migrate-test makemigrations clean dev dev-docker shell superuser docker-build docker-up docker-down docker-logs docker-shell docker-migrate docker-makemigrations docker-superuser

# Backend directory path
BACKEND_DIR = backend

# Load environment variables from .env file if it exists
# This loads variables into Make and exports them to subprocesses
ifneq (,$(wildcard .env))
    include .env
    export
endif

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --extra test

test: ## Run all tests with PostgreSQL (requires Docker)
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.test_settings uv run pytest

test-fast: ## Run tests with SQLite (faster, no Docker required)
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.test_settings_sqlite uv run pytest

test-local: ## Run tests with local PostgreSQL database (requires PostgreSQL running)
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.settings uv run pytest

test-ci: ## Run tests for CI (with coverage and PostgreSQL)
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.test_settings uv run pytest --cov=. --cov-report=xml --cov-report=html

test-ci-fast: ## Run tests for CI with SQLite (faster)
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.test_settings_sqlite uv run pytest --cov=. --cov-report=xml --cov-report=html

lint: ## Run linting checks
	cd $(BACKEND_DIR) && uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,venv,__pycache__,.git
	cd $(BACKEND_DIR) && uv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.venv,venv,__pycache__,.git

format: ## Format code with black and isort
	cd $(BACKEND_DIR) && uv run black .
	cd $(BACKEND_DIR) && uv run isort .

format-check: ## Check code formatting
	cd $(BACKEND_DIR) && uv run black --check .
	cd $(BACKEND_DIR) && uv run isort --check-only .

security: ## Run security checks
	cd $(BACKEND_DIR) && uv run bandit -r . -f json -o bandit-report.json --exclude .venv,venv,__pycache__,.git || true
	uv run safety check --json > safety-report.json || true

db-up: ## Start only the database container
	docker-compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 3

migrate: db-up ## Run database migrations (starts DB if needed)
	cd $(BACKEND_DIR) && uv run manage.py migrate

migrate-test: ## Run database migrations for tests
	cd $(BACKEND_DIR) && DJANGO_SETTINGS_MODULE=estimaite.test_settings uv run manage.py migrate

makemigrations: ## Create database migrations
	cd $(BACKEND_DIR) && uv run manage.py makemigrations

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf htmlcov
	rm -rf $(BACKEND_DIR)/htmlcov
	rm -rf .coverage
	rm -rf $(BACKEND_DIR)/.coverage
	rm -rf coverage.xml
	rm -rf $(BACKEND_DIR)/coverage.xml
	rm -rf bandit-report.json
	rm -rf safety-report.json
	rm -rf $(BACKEND_DIR)/bandit-report.json

dev: ## Start development server (local)
	cd $(BACKEND_DIR) && uv run manage.py runserver

dev-docker: ## Start development server with Docker (with hot-reload)
	docker-compose up --build

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker container logs
	docker-compose logs -f backend

docker-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

docker-migrate: ## Run migrations in Docker container
	docker-compose exec backend uv run manage.py migrate

docker-makemigrations: ## Create migrations in Docker container
	docker-compose exec backend uv run manage.py makemigrations

docker-superuser: ## Create superuser in Docker container
	docker-compose exec backend uv run manage.py createsuperuser

shell: ## Start Django shell (local)
	cd $(BACKEND_DIR) && uv run manage.py shell

superuser: ## Create superuser (local)
	cd $(BACKEND_DIR) && uv run manage.py createsuperuser
