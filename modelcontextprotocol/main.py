#!/usr/bin/env python3
"""JustiFi FastMCP Server - Multi-Transport Support

A FastMCP server that provides AI agents with tools to interact with the JustiFi API.
Supports stdio, HTTP, and SSE transports with automatic configuration.

Usage:
    # STDIO mode (default)
    python main.py

    # HTTP server mode
    MCP_TRANSPORT=http MCP_PORT=3000 python main.py

    # SSE server mode
    MCP_TRANSPORT=sse MCP_PORT=3000 python main.py

    # Health check
    python main.py --health-check
"""

import asyncio
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv

# Import FastMCP server and configuration
from .config import MCPConfig
from .server import create_mcp_server


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the FastMCP server."""
    logger = logging.getLogger()

    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        log_level = "INFO"

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Only log to stderr to avoid interfering with MCP stdio communication
            logging.StreamHandler(sys.stderr)
        ],
    )

    # Create logger for this module
    logger.info(f"Logging configured at {log_level} level")


async def health_check() -> dict[str, Any]:
    """Simple health check to verify FastMCP server creation and JustiFi API connectivity."""
    logger = logging.getLogger(__name__)

    try:
        logger.debug("Starting health check...")

        # Test FastMCP server creation
        mcp = create_mcp_server()
        logger.debug(f"FastMCP server created successfully: {type(mcp).__name__}")

        # Test JustiFi API connectivity by creating client
        from python.config import JustiFiConfig
        from python.core import JustiFiClient

        config = JustiFiConfig()
        client = JustiFiClient(
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        # Try to get access token to verify API connectivity
        token = await client.get_access_token()

        logger.debug("Health check completed successfully")

        return {
            "status": "healthy",
            "fastmcp_server": "created",
            "justifi_api": "connected",
            "token_acquired": bool(token),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def main():
    """Main entry point for FastMCP server."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))

    logger = logging.getLogger(__name__)
    logger.info("Starting JustiFi FastMCP Server initialization...")

    # Load environment variables
    load_dotenv()

    # Handle health check
    if "--health-check" in sys.argv:
        logger.info("Performing JustiFi FastMCP health check...")
        print("Performing JustiFi FastMCP health check...", file=sys.stderr)

        health_result = asyncio.run(health_check())

        if health_result["status"] == "healthy":
            logger.info("Health check passed")
            print("✅ JustiFi FastMCP server healthy", file=sys.stderr)
            print(f"📊 Details: {health_result}", file=sys.stderr)
        else:
            logger.error(f"Health check failed: {health_result['error']}")
            print(
                f"❌ JustiFi FastMCP health check failed: {health_result['error']}",
                file=sys.stderr,
            )
            sys.exit(1)
        return

    # Create FastMCP server
    try:
        mcp = create_mcp_server()
        logger.info("FastMCP server created successfully")
    except Exception as e:
        logger.error(f"Failed to create FastMCP server: {e}")
        print(f"❌ Failed to create FastMCP server: {e}", file=sys.stderr)
        sys.exit(1)

    # Load transport configuration
    config = MCPConfig.from_env()

    print("🚀 Starting JustiFi FastMCP Server...", file=sys.stderr)
    print(f"🌐 Transport: {config.transport}", file=sys.stderr)

    if config.transport == "stdio":
        print("📡 Using stdio transport (local AI clients)", file=sys.stderr)
    else:
        print(
            f"📡 Using {config.transport} transport on {config.host}:{config.port}",
            file=sys.stderr,
        )

    # Run FastMCP server with configured transport
    try:
        if config.transport == "stdio":
            mcp.run()
        elif config.transport == "http":
            mcp.run(transport="http", host=config.host, port=config.port)
        elif config.transport == "sse":
            mcp.run(transport="sse", host=config.host, port=config.port)
        else:
            raise ValueError(f"Unknown transport: {config.transport}")

    except Exception as e:
        logger.error(f"FastMCP server failed: {e}")
        print(f"❌ FastMCP server failed: {e}", file=sys.stderr)
        sys.exit(1)


def cli_main():
    """Console script entry point."""
    main()


if __name__ == "__main__":
    main()
