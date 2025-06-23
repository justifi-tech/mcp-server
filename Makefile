.PHONY: help install start stop clean test dev-start dev-stop dev-clean mcp-test env-check lint format type-check security check-all build-dev

# Default target
help:
	@echo "JustiFi MCP Server - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install     - Build development container with dependencies"
	@echo "  env-check   - Verify .env file exists"
	@echo ""
	@echo "Development:"
	@echo "  dev-start   - Start databases only (for local MCP development)"
	@echo "  dev-stop    - Stop development databases"
	@echo "  dev-clean   - Clean development environment"
	@echo ""
	@echo "Full Stack:"
	@echo "  start       - Start databases and management UIs"
	@echo "  stop        - Stop all services"
	@echo "  clean       - Clean all volumes and containers"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run unit tests (in container)"
	@echo "  mcp-test    - Test MCP server directly"
	@echo ""
	@echo "Code Quality (All in Docker):"
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
	docker-compose -f docker-compose.lint.yml build linter
	@echo "✅ Development container built"

# Install dependencies (build container)
install: build-dev
	@echo "✅ Dependencies installed in container"

# Development: databases only
dev-start: env-check
	@echo "Starting development databases..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development databases started"
	@echo "📊 PgAdmin: http://localhost:5050 (admin@example.com / admin)"

dev-stop:
	@echo "Stopping development databases..."
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ Development databases stopped"

dev-clean:
	@echo "Cleaning development environment..."
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
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
	docker-compose -f docker-compose.lint.yml down -v --remove-orphans
	@echo "✅ All volumes and containers cleaned"

# Testing (in container)
test: env-check
	@echo "🧪 Running unit tests in container..."
	docker-compose -f docker-compose.lint.yml run --rm linter sh -c "pytest tests/ -v && echo '✅ Tests completed'"

# Code Quality Targets (All in Docker)
format: env-check
	@echo "🎨 Formatting code in container..."
	docker-compose -f docker-compose.lint.yml run --rm formatter

lint: env-check
	@echo "🔍 Running ruff linter in container..."
	docker-compose -f docker-compose.lint.yml run --rm ruff

type-check: env-check
	@echo "🔍 Running mypy type checking in container..."
	docker-compose -f docker-compose.lint.yml run --rm mypy

security: env-check
	@echo "🔒 Running bandit security scan in container..."
	docker-compose -f docker-compose.lint.yml run --rm bandit

check-all: env-check
	@echo "🔍 Running all code quality checks in container..."
	docker-compose -f docker-compose.lint.yml run --rm check-all

# Test MCP server directly
mcp-test: env-check
	@echo "Testing MCP server..."
	@echo "Note: This will run the MCP server in stdio mode."
	@echo "Use Ctrl+C to stop the server."
	python main.py

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