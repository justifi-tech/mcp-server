#!/bin/bash

# JustiFi MCP Server Wrapper Script
# This script runs the MCP server locally for Claude Desktop
# 
# For development with auto-restart, use: make dev
# For full development commands, see: make help

# Change to the script directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from env.example:" >&2
    echo "   cp env.example .env" >&2
    echo "   # Then edit .env with your API keys" >&2
    exit 1
fi

# Ensure dependencies are installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:" >&2
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# Install dependencies if needed
echo "🔧 Ensuring dependencies are installed..."
uv pip install --system -e ".[dev]" --quiet 2>/dev/null || uv pip install -e ".[dev]" --quiet

# Run the MCP server locally with STDIO transport (override HTTP setting)
export MCP_TRANSPORT=stdio
exec uv run python main.py 