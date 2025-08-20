.PHONY: help setup dev test shell format lint clean logs drift-check version-check

# Default target
help:
	@echo "JustiFi MCP Server - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup       - Set up local development environment"
	@echo ""
	@echo "Development:"
	@echo "  dev         - Start MCP server with auto-restart"
	@echo "  shell       - Open interactive development shell"
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

# Set up local development environment
setup: env-check
	@if [ ! -d ".venv" ] || ! uv run python -c "import pytest" 2>/dev/null; then \
		echo "🔧 Setting up local development environment..." \
		echo "🐍 Creating virtual environment..." \
		uv venv .venv --quiet || true \
		echo "📦 Installing dependencies with uv..." \
		uv pip install -e ".[dev]" \
		echo "✅ Local development environment ready" \
	else \
		echo "✅ Development environment already set up"; \
	fi

# Start MCP server with auto-restart
dev: env-check setup
	@echo "🚀 Starting MCP server with auto-restart..."
	@echo "💡 Server will automatically restart when Python files change"
	@echo "🛑 Press Ctrl+C to stop"
	uv run watchmedo auto-restart --directory . --patterns "*.py" --recursive -- python main.py

# Interactive development shell
shell: env-check setup
	@echo "🐚 Opening interactive development shell..."
	@echo "💡 Virtual environment is activated. Type 'exit' to leave."
	@bash -c "source $$(uv venv --quiet) && exec bash"

# Run all tests
test: env-check setup
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

# Linting and formatting
lint: setup
	@echo "🔍 Running ruff linter..."
	uv run ruff check .

format: setup
	@echo "🎨 Formatting code with ruff..."
	uv run ruff format .

# GitHub Actions CI checks (format + lint exactly like CI)
ci-lint: env-check setup
	@echo "🔍 Running GitHub Actions CI checks..."
	@echo "1️⃣ Running ruff check..."
	uv run ruff check .
	@echo "2️⃣ Running ruff format --check..."
	uv run ruff format --check .
	@echo "✅ All CI linting checks passed!"

# Run all quality checks
check-all: lint format test

# Check for JustiFi API drift/changes
drift-check: env-check setup
	@echo "🔍 Checking for JustiFi API changes..."
	uv run python scripts/ci-drift-check.py

# Check version synchronization
version-check: setup
	@echo "🔍 Checking version synchronization..."
	./scripts/check-version-sync.sh 
