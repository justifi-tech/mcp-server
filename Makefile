.PHONY: help install start stop clean test dev-start dev-stop dev-clean mcp-test env-check lint format type-check security check-all build-dev eval

# Default target
help:
	@echo "JustiFi MCP Server - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install     - Build development container with dependencies"
	@echo "  env-check   - Verify .env file exists"
	@echo ""
	@echo "Development:"
	@echo "  dev-start   - Start unified dev container with databases"
	@echo "  dev-stop    - Stop development environment"
	@echo "  dev-clean   - Clean development environment"
	@echo "  shell       - Open interactive shell in dev container"
	@echo ""
	@echo "Full Stack:"
	@echo "  start       - Start databases and management UIs"
	@echo "  stop        - Stop all services"
	@echo "  clean       - Clean all volumes and containers"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run unit tests (in container)"
	@echo "  eval        - Run AI evaluation suite"
	@echo "  mcp-test    - Test MCP server directly"
	@echo "  drift-check - Check for JustiFi API changes"
	@echo "  drift-update - Check for API changes and update spec"
	@echo ""
	@echo "Code Quality (All in dev container):"
	@echo "  format      - Auto-format code with black and ruff"
	@echo "  lint        - Run ruff linter"
	@echo "  type-check  - Run mypy type checking"
	@echo "  security    - Run bandit security scan"
	@echo "  check-all   - Run all code quality checks"
	@echo ""
	@echo "Build:"
	@echo "  build-dev   - Build development container"
	@echo ""
	@echo "Note: MCP server runs via stdio transport, not as a web service."
	@echo "Configure Cursor to connect to: python main.py"
	@echo ""
	@echo "Production (standalone Docker):"
	@echo "  prod-build  - Build production container"
	@echo "  prod-run    - Run production container interactively"
	@echo "  prod-start  - Start production container in background"
	@echo "  prod-stop   - Stop production container"
	@echo "  prod-health - Check production container health"
	@echo "  prod-logs   - View production container logs"

# Environment check
env-check:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please create it from env.example:"; \
		echo "   cp env.example .env"; \
		echo "   # Then edit .env with your API keys"; \
		exit 1; \
	fi
	@echo "✅ .env file exists"

# Build development container with all tools
build-dev: env-check
	@echo "🔨 Building development container..."
	docker-compose build dev
	@echo "✅ Development container built"

# Install dependencies (build container)
install: build-dev
	@echo "✅ Dependencies installed in container"

# Development: unified container with databases
dev-start: env-check
	@echo "Starting development environment..."
	docker-compose up -d postgres redis pgadmin redis-commander
	@echo "✅ Development environment started"
	@echo "📊 PgAdmin: http://localhost:8080 (admin@justifi.local / admin123)"
	@echo "📊 Redis Commander: http://localhost:8082"
	@echo "🔧 Interactive shell: make shell"
	@echo "🚀 Auto-restart MCP server: make dev"

# Start MCP server with auto-restart on file changes
dev: env-check
	@echo "🚀 Starting MCP server with auto-restart..."
	@echo "💡 Server will automatically restart when Python files change"
	@echo "🛑 Press Ctrl+C to stop"
	docker-compose up mcp-dev

# Interactive development shell
shell: env-check
	@echo "🐚 Opening interactive development shell..."
	docker-compose run --rm dev bash

dev-stop:
	@echo "Stopping development environment..."
	docker-compose down
	@echo "✅ Development environment stopped"

dev-clean:
	@echo "Cleaning development environment..."
	docker-compose down -v --remove-orphans
	@echo "✅ Development environment cleaned"

# Full stack: databases + management UIs
start: env-check
	@echo "Starting full stack..."
	docker-compose up -d
	@echo "✅ Full stack started"
	@echo "📊 PgAdmin: http://localhost:5050 (admin@example.com / admin)"
	@echo "📊 Redis Commander: http://localhost:8082"

stop:
	@echo "Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped"

clean:
	@echo "Cleaning all volumes and containers..."
	docker-compose down -v --remove-orphans
	@echo "✅ All volumes and containers cleaned"

# Testing (in dev container)
test: env-check
	@echo "🧪 Running unit tests in dev container..."
	docker-compose run --rm dev pytest tests/ -v

# Code Quality Targets (All in dev container)
format: env-check
	@echo "🎨 Formatting code in dev container..."
	docker-compose run --rm dev sh -c "black . && ruff check --fix --select I ."

lint: env-check
	@echo "🔍 Running ruff linter in dev container..."
	docker-compose run --rm dev ruff check .

type-check: env-check
	@echo "🔍 Running mypy type checking in dev container..."
	docker-compose run --rm dev mypy .

security: env-check
	@echo "🔒 Running bandit security scan in dev container..."
	docker-compose run --rm dev bandit -r .

check-all: env-check
	@echo "🔍 Running all code quality checks in dev container..."
	docker-compose run --rm dev sh -c "ruff check . && mypy ."

# Pre-commit setup
pre-commit-install: env-check
	@echo "🔧 Installing pre-commit hooks..."
	docker-compose run --rm dev pre-commit install
	@echo "✅ Pre-commit hooks installed"

pre-commit-run: env-check
	@echo "🔍 Running pre-commit on all files..."
	docker-compose run --rm dev pre-commit run --all-files

# Modern Python development
install-dev: env-check
	@echo "📦 Installing development dependencies..."
	docker-compose run --rm dev uv pip install -e ".[dev]"
	@echo "✅ Development dependencies installed"

test-coverage: env-check
	@echo "🧪 Running tests with coverage..."
	docker-compose run --rm dev pytest tests/ --cov=tools --cov-report=html --cov-report=term-missing

docs-serve: env-check
	@echo "📚 Starting documentation server..."
	docker-compose run --rm -p 8080:8080 dev mkdocs serve -a 0.0.0.0:8080

# Note: shell command moved above to avoid duplication

# Test MCP server directly
mcp-test: env-check
	@echo "Testing MCP server..."
	@echo "Note: This will run the MCP server in stdio mode."
	@echo "Use Ctrl+C to stop the server."
	python main.py

# Check for JustiFi API drift
drift-check: env-check
	@echo "🔍 Checking for JustiFi API changes..."
	docker-compose run --rm dev python scripts/check-api-drift.py

# Check for API drift and update spec if no breaking changes
drift-update: env-check
	@echo "🔍 Checking for JustiFi API changes and updating spec..."
	docker-compose run --rm dev python scripts/check-api-drift.py --update-spec

# Production deployment commands (standalone Docker)
prod-build: env-check
	@echo "🔨 Building production container..."
	docker build --target production -t justifi-mcp:latest .
	@echo "✅ Production container built"

prod-run: env-check prod-build
	@echo "🚀 Running production container..."
	@echo "Note: This will run interactively. Use Ctrl+C to stop."
	docker run -it --name justifi-mcp-server \
		--env-file .env \
		--rm \
		justifi-mcp:latest

prod-start: env-check prod-build
	@echo "🚀 Starting production container in background..."
	docker run -d --name justifi-mcp-server \
		--env-file .env \
		--restart unless-stopped \
		justifi-mcp:latest
	@echo "✅ Production container started"
	@echo "📊 Health check: make prod-health"
	@echo "📋 Logs: make prod-logs"

prod-stop:
	@echo "🛑 Stopping production container..."
	@docker stop justifi-mcp-server 2>/dev/null || true
	@docker rm justifi-mcp-server 2>/dev/null || true
	@echo "✅ Production container stopped"

prod-health:
	@echo "🩺 Checking production container health..."
	@docker exec justifi-mcp-server python main.py --health 2>/dev/null | jq . || echo "❌ Container not running or unhealthy"

prod-logs:
	@echo "📋 Production container logs:"
	@docker logs justifi-mcp-server --tail=50 -f 2>/dev/null || echo "❌ Container not running"

prod-clean:
	@echo "🧹 Cleaning production containers and images..."
	@docker stop justifi-mcp-server 2>/dev/null || true
	@docker rm justifi-mcp-server 2>/dev/null || true
	@docker rmi justifi-mcp:latest 2>/dev/null || true
	@echo "✅ Production environment cleaned"

# Quick setup for new developers
setup: env-check install dev-start
	@echo "🎉 Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure Cursor to connect to this MCP server:"
	@echo "   Command: python"
	@echo "   Args: [\"$(PWD)/main.py\"]"
	@echo "   Working Directory: $(PWD)"
	@echo ""
	@echo "2. Test the server: make mcp-test"

# Run AI evaluation suite
eval: env-check build-dev
	@echo "📈 Running AI evaluation suite in dev container..."
	docker-compose run --rm dev python scripts/run-evals.py 