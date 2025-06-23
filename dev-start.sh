#!/bin/bash

# MCP Server Development Startup Script
# This runs databases in Docker and the MCP server locally for faster development

set -e

echo "🚀 Starting MCP Server Development Environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating one from env.example..."
    cp env.example .env
    echo "📝 Please edit .env with your API keys before continuing"
    echo "   Required: OPENAI_API_KEY"
    echo "   Optional: LANGCHAIN_API_KEY (for tracing)"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start databases only
echo "🔨 Starting databases (Postgres + Redis)..."
docker compose -f docker-compose.dev.yml up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 5

# Check database health
echo "🔍 Checking database health..."

# Check Postgres
if docker compose -f docker-compose.dev.yml exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Postgres is ready"
else
    echo "❌ Postgres is not ready"
    exit 1
fi

# Check Redis
if docker compose -f docker-compose.dev.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
    exit 1
fi

# Set up local environment
echo "🐍 Setting up Python environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment and install dependencies
source .venv/bin/activate
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Update .env with Docker database URLs
echo "📝 Updating .env with Docker database URLs..."
sed -i.bak 's|DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5434/mcp|' .env
sed -i.bak 's|REDIS_URL=.*|REDIS_URL=redis://localhost:6380/0|' .env

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📍 Database services:"
echo "   • Postgres:        localhost:5434"
echo "   • Redis:           localhost:6380"
echo "   • PgAdmin:         http://localhost:5050 (admin@example.com / admin)"
echo "   • Redis Commander: http://localhost:8082"
echo ""
echo "🚀 To start the MCP server:"
echo "   source .venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "🔗 Then configure Cursor:"
echo "   • Remote Agent URL: http://localhost:8000/chat/stream"
echo "   • Method: GET"
echo "   • Query Params: session_id=\${tabId}"
echo ""
echo "📋 Useful commands:"
echo "   • Stop databases:  docker compose -f docker-compose.dev.yml down"
echo "   • View DB logs:    docker compose -f docker-compose.dev.yml logs postgres"
echo "   • View Redis logs: docker compose -f docker-compose.dev.yml logs redis"
echo "" 