.PHONY: help dev test shell format lint clean build logs

# Default target
help:
	@echo "JustiFi MCP Server - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev         - Start MCP server with auto-restart"
	@echo "  shell       - Open interactive development shell"
	@echo "  logs        - View logs"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run all tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  format      - Auto-format code with ruff"
	@echo "  lint        - Run ruff linter"
	@echo "  ci-lint     - Run GitHub Actions CI checks (lint + format check)"
	@echo ""
	@echo "Utilities:"
	@echo "  build       - Build development container"
	@echo "  clean       - Clean up containers and volumes"
	@echo "  drift-check - Check for JustiFi API changes"
	@echo "  version-check - Check version synchronization"
	@echo ""
	@echo "Note: Configure Cursor to connect to: python main.py"

# Environment check
env-check:
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please create it from env.example:"; \
		echo "   cp env.example .env"; \
		echo "   # Then edit .env with your API keys"; \
		exit 1; \
	fi
	@echo "✅ .env file exists"

# Build development container
build: env-check
	@echo "🔨 Building development container..."
	docker-compose build dev
	@echo "✅ Development container built"

# Start MCP server with auto-restart
dev: env-check build
	@echo "🚀 Starting MCP server with auto-restart..."
	@echo "💡 Server will automatically restart when Python files change"
	@echo "🛑 Press Ctrl+C to stop"
	docker-compose up mcp-dev -d

logs:
	@echo "🔍 Viewing logs..."
	docker-compose logs -f mcp-dev

# Interactive development shell
shell: env-check build
	@echo "🐚 Opening interactive development shell..."
	docker-compose run --rm dev bash

# Run all tests
test: env-check build
	@echo "🧪 Running tests..."
	docker-compose run --rm dev pytest tests/ -v

# Linting and formatting
lint:
	docker-compose run --rm dev ruff check .

format:
	docker-compose run --rm dev ruff format .

# GitHub Actions CI checks (format + lint exactly like CI)
ci-lint: env-check build
	@echo "🔍 Running GitHub Actions CI checks..."
	@echo "1️⃣ Running ruff check..."
	docker-compose run --rm dev ruff check .
	@echo "2️⃣ Running ruff format --check..."
	docker-compose run --rm dev ruff format --check .
	@echo "✅ All CI linting checks passed!"

# Run all quality checks (excluding mypy)
check-all: lint format test

# Clean up containers and volumes
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v --remove-orphans
	@echo "✅ Cleanup complete"

# Check for JustiFi API drift/changes
drift-check: env-check
	@echo "🔍 Checking for JustiFi API changes..."
	python scripts/ci-drift-check.py

# Check version synchronization
version-check:
	@echo "🔍 Checking version synchronization..."
	./scripts/check-version-sync.sh 