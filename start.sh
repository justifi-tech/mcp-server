#!/bin/bash

# JustiFi MCP Server - Production Startup Script
# This script starts the MCP server in production mode

set -e

echo "🚀 Starting JustiFi MCP Server (Production)"

# Check if running in container
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    
    # Validate required environment variables
    REQUIRED_VARS=("JUSTIFI_CLIENT_ID" "JUSTIFI_CLIENT_SECRET")
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Error: Required environment variable $var is not set"
            exit 1
        fi
    done
    
    echo "✅ Environment variables validated"
    
    # Set defaults for optional variables
    export JUSTIFI_BASE_URL="${JUSTIFI_BASE_URL:-https://api.justifi.ai/v1}"
    export LANGCHAIN_TRACING_V2="${LANGCHAIN_TRACING_V2:-false}"
    
    # Run health check first
    echo "🩺 Running health check..."
    if python main.py --health > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed, but continuing..."
    fi
    
    # Start the MCP server
    echo "🎯 Starting MCP server..."
    exec python main.py
    
else
    echo "🏠 Running locally - use 'make dev-start' for development"
    echo "Or build and run the Docker container:"
    echo "  docker build -t justifi-mcp:latest ."
    echo "  docker run -it --env-file .env justifi-mcp:latest"
    exit 1
fi 