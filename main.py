#!/usr/bin/env python3
"""JustiFi MCP Server - Payout Focus

A Model Context Protocol server focused on JustiFi payout operations.
This version is designed for evaluation and testing of payout-specific functionality.
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import stdio_server
from mcp.server import Server
from mcp.types import (
    Prompt,
    Resource,
    TextContent,
    Tool,
)

# Import our focused payout tools from standard package structure
from justifi_mcp.core import JustiFiClient
from justifi_mcp.payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)

# Initialize the MCP server
server: Server = Server("justifi-payout-mcp-server")

# Tool dispatch dictionary - focused on payout operations only
PAYOUT_TOOL_DISPATCH = {
    "retrieve_payout": retrieve_payout,
    "list_payouts": list_payouts,
    "get_payout_status": get_payout_status,
    "get_recent_payouts": get_recent_payouts,
}


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available JustiFi payout tools."""
    return [
        Tool(
            name="retrieve_payout",
            description="Retrieve details of a specific payout by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "payout_id": {
                        "type": "string",
                        "description": "The ID of the payout to retrieve (e.g., 'po_ABC123XYZ')",
                    }
                },
                "required": ["payout_id"],
            },
        ),
        Tool(
            name="list_payouts",
            description="List payouts with cursor-based pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of payouts to return (default: 25, max: 100)",
                        "default": 25,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "after_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get payouts after this cursor)",
                        "optional": True,
                    },
                    "before_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get payouts before this cursor)",
                        "optional": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_payout_status",
            description="Get the status of a specific payout (returns just the status string)",
            inputSchema={
                "type": "object",
                "properties": {
                    "payout_id": {
                        "type": "string",
                        "description": "The ID of the payout to check status for",
                    }
                },
                "required": ["payout_id"],
            },
        ),
        Tool(
            name="get_recent_payouts",
            description="Get the most recent payouts (optimized for recency)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent payouts to return (default: 10, max: 25)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 25,
                    }
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls using our focused payout dispatch."""
    if name not in PAYOUT_TOOL_DISPATCH:
        return [
            TextContent(
                type="text",
                text=f"Unknown tool: {name}. Available payout tools: {list(PAYOUT_TOOL_DISPATCH.keys())}",
            )
        ]

    try:
        # Create JustiFi client instance
        client = JustiFiClient()

        # Get the tool function
        tool_func = PAYOUT_TOOL_DISPATCH[name]

        # Call the tool function with client as first argument
        result = await tool_func(client, **arguments)  # type: ignore[operator]

        # Format the response
        response_text = json.dumps(result, indent=2)

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        error_msg = f"Error calling {name}: {type(e).__name__}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources (empty for now)."""
    return []


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """List available prompts (empty for now)."""
    return []


async def health_check():
    """Simple health check to verify JustiFi API connectivity."""
    try:
        client = JustiFiClient()
        token = await client.get_access_token()
        return {"status": "healthy", "token_acquired": bool(token)}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def main():
    """Main entry point for the payout-focused MCP server."""
    # Load environment variables
    load_dotenv()

    # Verify required environment variables
    required_vars = ["JUSTIFI_CLIENT_ID", "JUSTIFI_CLIENT_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {missing_vars}",
            file=sys.stderr,
        )
        print("Please set these in your .env file or environment", file=sys.stderr)
        sys.exit(1)

    # Optional health check on startup
    if "--health-check" in sys.argv:
        print("Performing JustiFi API health check...", file=sys.stderr)
        health_result = await health_check()
        if health_result["status"] == "healthy":
            print("✅ JustiFi API connection successful", file=sys.stderr)
        else:
            print(
                f"❌ JustiFi API connection failed: {health_result['error']}",
                file=sys.stderr,
            )
            sys.exit(1)

    print("🚀 Starting JustiFi Payout MCP Server...", file=sys.stderr)
    print(
        "📊 Available tools: retrieve_payout, list_payouts, get_payout_status, get_recent_payouts",
        file=sys.stderr,
    )

    # Run the stdio server
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
