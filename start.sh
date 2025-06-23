#!/bin/bash

# MCP Server Docker Startup Script

set -e

echo "🚀 Starting MCP Server Docker Stack..."

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

# Build and start the stack
echo "🔨 Building and starting containers..."
docker compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Postgres
if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Postgres is ready"
else
    echo "❌ Postgres is not ready"
fi

# Check Redis
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check MCP Server
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ MCP Server is ready"
else
    echo "❌ MCP Server is not ready"
fi

echo ""
echo "🎉 MCP Server Stack is running!"
echo ""
echo "📍 Available services:"
echo "   • MCP Server:      http://localhost:8000"
echo "   • Health Check:    http://localhost:8000/health"
echo "   • API Docs:        http://localhost:8000/docs"
echo "   • PgAdmin:         http://localhost:5050 (admin@example.com / admin)"
echo "   • Redis Commander: http://localhost:8081"
echo ""
echo "🔗 Cursor Integration:"
echo "   • Remote Agent URL: http://localhost:8000/chat/stream"
echo "   • Method: GET"
echo "   • Query Params: session_id=\${tabId}"
echo ""
echo "📋 Useful commands:"
echo "   • View logs:    docker compose logs -f"
echo "   • Stop stack:   docker compose down"
echo "   • Restart:      docker compose restart"
echo "" 