.PHONY: help install dev test lint format docker-up docker-down clean

help: ## Display this help message
	@echo "AKRIN AI Chatbot - Development Commands"
	@echo "======================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt
	python -m spacy download en_core_web_md
	npm install
	cp .env.example .env
	@echo "Installation complete. Please update .env with your API keys."

dev: ## Run development server
	docker-compose up -d postgres mongodb redis
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v --cov=src --cov-report=html

lint: ## Run linting
	flake8 src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

docker-up: ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

migrate: ## Run database migrations
	alembic upgrade head

seed-knowledge: ## Seed knowledge base with initial data
	python scripts/seed_knowledge_base.py

train-nlu: ## Train NLU models
	python scripts/train_nlu.py

build: ## Build production Docker image
	docker build -t akrin-chatbot:latest .

deploy-dev: ## Deploy to development environment
	./scripts/deploy.sh dev

deploy-prod: ## Deploy to production environment
	./scripts/deploy.sh prod

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

monitor: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Kibana: http://localhost:5601"

benchmark: ## Run performance benchmarks
	python scripts/benchmark.py

security-scan: ## Run security scan
	bandit -r src/
	safety check