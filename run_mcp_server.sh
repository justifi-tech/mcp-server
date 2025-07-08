#!/bin/bash

# JustiFi MCP Server Wrapper Script
# This script runs the MCP server in a Docker container for Claude Desktop

# Change to the script directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from env.example:" >&2
    echo "   cp env.example .env" >&2
    echo "   # Then edit .env with your API keys" >&2
    exit 1
fi

# Run the MCP server in a container with STDIO transport (override HTTP setting)
exec docker-compose run --rm -T -e MCP_TRANSPORT=stdio dev python main.py 