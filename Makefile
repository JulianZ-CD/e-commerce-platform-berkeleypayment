# Makefile for E-commerce API
# One-stop solution for all development operations

.PHONY: help build up down logs test clean restart init-db dev check-docker create-testdb push setup-buildx

# Default target - show help
.DEFAULT_GOAL := help

# Configuration
REGISTRY := ghcr.io
IMAGE_NAME := julianz-cd/e-commerce-platform-api
IMAGE_TAG := latest
PLATFORMS := linux/amd64,linux/arm64

help: ## Show this help message
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║      E-commerce API - Available Commands            ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Setup & Start:"
	@echo "  make up         - Start all services (PostgreSQL + API)"
	@echo "  make dev        - Start local development setup"
	@echo "  make init-db    - Initialize database tables"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test       - Run all tests (creates test DB automatically)"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-int   - Run integration tests only"
	@echo ""
	@echo "🔧 Operations:"
	@echo "  make logs       - View API logs"
	@echo "  make restart    - Restart all services"
	@echo "  make down       - Stop all services"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make build      - Rebuild Docker images"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  make setup-buildx - Setup Docker buildx for multi-platform"
	@echo "  make push       - Build & push multi-platform images to registry"
	@echo "  make pull-image - Pull pre-built image from registry"
	@echo "  make up-remote  - Start services using pre-built image (no local build)"
	@echo ""
	@echo "📊 Status:"
	@echo "  make status     - Check service status"
	@echo "  make ps         - List running containers"
	@echo ""
	@echo "💡 Quick Start: make up"
	@echo ""

check-docker: ## Verify Docker is running
	@if ! docker info > /dev/null 2>&1; then \
		echo "❌ Error: Docker is not running"; \
		echo "Please start Docker Desktop and try again"; \
		exit 1; \
	fi

build: check-docker ## Build Docker images
	@echo "🔨 Building Docker images..."
	@docker-compose build

up: check-docker ## Start all services
	@echo "🚀 Starting services..."
	@docker-compose up -d
	@echo ""
	@echo "⏳ Waiting for services to be ready..."
	@sleep 3
	@echo ""
	@echo "✅ Services started successfully!"
	@echo ""
	@echo "📍 Access Points:"
	@echo "   🌐 API:        http://localhost:8000"
	@echo "   📚 Swagger:    http://localhost:8000/docs"
	@echo "   📖 ReDoc:      http://localhost:8000/redoc"
	@echo "   🏥 Health:     http://localhost:8000/health"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   - Run tests:    make test"
	@echo "   - View logs:    make logs"
	@echo "   - Stop:         make down"
	@echo ""

down: ## Stop all services
	@echo "🛑 Stopping services..."
	@docker-compose down

init-db: ## Initialize database tables
	@echo "🗄️  Initializing database..."
	@python init_db.py
	@echo "✅ Database initialized!"

create-testdb: check-docker ## Create test database
	@echo "🧪 Creating test database..."
	@docker-compose exec -T postgres psql -U ecommerce_user -d postgres -c "DROP DATABASE IF EXISTS ecommerce_test_db;" 2>/dev/null || true
	@docker-compose exec -T postgres psql -U ecommerce_user -d postgres -c "CREATE DATABASE ecommerce_test_db OWNER ecommerce_user;" 2>/dev/null || true
	@echo "✅ Test database created!"

test: create-testdb ## Run all tests
	@echo "🧪 Running all tests..."
	@echo ""
	@python -m pytest tests/ -v --tb=short
	@echo ""
	@echo "✅ All tests completed!"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	@python -m pytest tests/unit/ -v

test-int: create-testdb ## Run integration tests only
	@echo "🧪 Running integration tests..."
	@python -m pytest tests/integration/ -v

logs: ## View API logs (Ctrl+C to exit)
	@echo "📋 Viewing logs (press Ctrl+C to exit)..."
	@docker-compose logs -f api

logs-db: ## View PostgreSQL logs
	@docker-compose logs -f postgres

logs-all: ## View all logs
	@docker-compose logs -f

status: ## Check service status
	@echo "📊 Service Status:"
	@echo ""
	@docker-compose ps

ps: status ## Alias for status

restart: down up ## Restart all services
	@echo "✅ Services restarted!"

clean: ## Remove containers and volumes
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@echo "🗑️  Removing Python cache..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

dev: ## Setup local development environment
	@echo "🔧 Setting up local development environment..."
	@echo ""
	@echo "1️⃣  Starting PostgreSQL..."
	@docker-compose up -d postgres
	@echo "   Waiting for PostgreSQL..."
	@sleep 3
	@echo ""
	@echo "2️⃣  Initializing database..."
	@$(MAKE) init-db
	@echo ""
	@echo "✅ Development setup complete!"
	@echo ""
	@echo "📍 Next steps:"
	@echo "   1. Activate venv:     source venv/bin/activate"
	@echo "   2. Start API:         uvicorn app.main:app --reload"
	@echo "   3. Or just use:       make up"
	@echo ""

shell: ## Open Python shell with app context
	@python -i -c "from app.database import SessionLocal; from app.models import *; db = SessionLocal()"

db-shell: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U ecommerce_user -d ecommerce_db

rebuild: clean build up ## Full rebuild (clean + build + up)
	@echo "✅ Full rebuild complete!"

health: ## Check API health
	@echo "🏥 Checking API health..."
	@curl -s http://localhost:8000/health | python -m json.tool

# Development helpers
.PHONY: venv install format lint

venv: ## Create Python virtual environment
	@python3 -m venv venv
	@echo "✅ Virtual environment created!"
	@echo "Activate with: source venv/bin/activate"

install: ## Install Python dependencies
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Docker buildx for multi-platform builds
setup-buildx: check-docker ## Setup Docker buildx for multi-platform builds
	@echo "🔧 Setting up Docker buildx..."
	@docker buildx create --name ecommerce-builder --use 2>/dev/null || \
		docker buildx use ecommerce-builder 2>/dev/null || \
		echo "Buildx builder already exists"
	@docker buildx inspect --bootstrap
	@echo "✅ Buildx ready for multi-platform builds!"

push: check-docker ## Build and push multi-platform images to registry
	@echo "🚀 Building and pushing multi-platform images..."
	@echo ""
	@echo "Target platforms: $(PLATFORMS)"
	@echo "Registry: $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"
	@echo ""
	@echo "⚠️  Make sure you are logged in to GitHub Container Registry:"
	@echo "   docker login ghcr.io -u USERNAME"
	@echo ""
	@read -p "Press Enter to continue or Ctrl+C to cancel..." dummy
	@echo ""
	@echo "🔨 Building for multiple platforms..."
	@docker buildx build \
		--platform $(PLATFORMS) \
		--file Dockerfile \
		--tag $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) \
		--push \
		.
	@echo ""
	@echo "✅ Image pushed successfully!"
	@echo "   Image: $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"
	@echo "   Platforms: $(PLATFORMS)"
	@echo ""
	@echo "To use this image, update docker-compose.yml:"
	@echo "  image: $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"
	@echo ""

pull-image: check-docker ## Pull pre-built image from registry
	@echo "📥 Pulling pre-built image from registry..."
	@echo ""
	@echo "Image: $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"
	@echo ""
	@docker pull $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo ""
	@echo "✅ Image pulled successfully!"
	@echo "   You can now use 'make up-remote' to start services"
	@echo ""

up-remote: check-docker pull-image ## Start services using pre-built image (no local build)
	@echo "🚀 Starting services with pre-built image..."
	@echo ""
	@echo "Using image: $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)"
	@echo ""
	@COMPOSE_IMAGE=$(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) \
		docker-compose -f docker-compose.yml -f docker-compose.remote.yml up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Access points:"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo ""
	@echo "💡 Tips:"
	@echo "   - View logs: make logs"
	@echo "   - Stop services: make down"
	@echo ""

