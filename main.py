#!/usr/bin/env python3
"""JustiFi MCP Server - Configuration-Driven Payment Integration

A Model Context Protocol (MCP) server that provides AI agents with tools
to interact with the JustiFi payment API. Now supports Stripe-like configuration
for flexible tool selection and context management.

Usage:
    # Basic usage (no tools enabled - secure by default)
    python main.py

    # With health check
    python main.py --health-check

    # With tool selection (container-friendly)
    JUSTIFI_ENABLED_TOOLS=all python main.py
    JUSTIFI_ENABLED_TOOLS="retrieve_payout,list_payouts" python main.py
"""
import asyncio
import os
import sys
from typing import Any

from dotenv import load_dotenv
from mcp import stdio_server

# Import the new toolkit system
from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit


async def health_check(toolkit: JustiFiToolkit) -> dict[str, Any]:
    """Simple health check to verify JustiFi API connectivity."""
    try:
        # Create a temporary MCP adapter to access the client
        from justifi_mcp.adapters.mcp import MCPAdapter

        adapter = MCPAdapter(toolkit.config)
        token = await adapter.client.get_access_token()
        config_summary = toolkit.get_configuration_summary()

        return {
            "status": "healthy",
            "token_acquired": bool(token),
            "configuration": config_summary,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def load_configuration() -> JustiFiConfig:
    """Load configuration from environment variables (container-friendly)."""
    # Check for custom tool configuration via environment variable
    enabled_tools_env = os.getenv("JUSTIFI_ENABLED_TOOLS")
    if enabled_tools_env:
        if enabled_tools_env.lower() == "all":
            return JustiFiConfig(enabled_tools="all")
        else:
            # Parse comma-separated list
            enabled_tools_list = [tool.strip() for tool in enabled_tools_env.split(",")]
            return JustiFiConfig(enabled_tools=enabled_tools_list)

    # Default configuration (no tools enabled - secure by default)
    return JustiFiConfig()


async def main():
    """Main entry point for the configuration-driven MCP server."""
    # Load environment variables
    load_dotenv()

    # Load configuration
    try:
        config = load_configuration()
    except Exception as e:
        print(f"Error: Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Create toolkit with configuration
    try:
        toolkit = JustiFiToolkit(config=config)
    except Exception as e:
        print(f"Error: Failed to initialize toolkit: {e}", file=sys.stderr)
        print(
            "Please check your JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET",
            file=sys.stderr,
        )
        sys.exit(1)

    # Optional health check on startup
    if "--health-check" in sys.argv:
        print("Performing JustiFi API health check...", file=sys.stderr)
        health_result = await health_check(toolkit)

        if health_result["status"] == "healthy":
            print("✅ JustiFi API connection successful", file=sys.stderr)
            print(
                f"📊 Configuration: {health_result['configuration']}", file=sys.stderr
            )
        else:
            print(
                f"❌ JustiFi API connection failed: {health_result['error']}",
                file=sys.stderr,
            )
            sys.exit(1)

    # Get configuration summary for startup info
    config_summary = toolkit.get_configuration_summary()
    enabled_tools = config_summary["enabled_tools"]

    print(
        "🚀 Starting JustiFi MCP Server with Configuration Support...", file=sys.stderr
    )
    print(f"🌍 Environment: {config_summary['environment']}", file=sys.stderr)
    print(
        f"📊 Enabled tools ({len(enabled_tools)}): {', '.join(enabled_tools)}",
        file=sys.stderr,
    )
    print(f"⚡ Base URL: {config_summary['base_url']}", file=sys.stderr)
    print(f"⏱️  Timeout: {config_summary['timeout']}s", file=sys.stderr)

    # Get the configured MCP server
    server = toolkit.get_mcp_server("justifi-mcp-server")

    # Run the stdio server
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())


def cli_main():
    """Console script entry point."""
    asyncio.run(main())
