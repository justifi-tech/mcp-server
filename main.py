#!/usr/bin/env python3
"""
JustiFi MCP Server

A Model Context Protocol server that provides tools for interacting with the JustiFi payments API.
Supports OAuth2 Client-Credentials authentication with token caching.
"""
import asyncio
import os

from dotenv import load_dotenv
from mcp import stdio_server
from mcp.server import Server
from mcp.types import (
    Prompt,
    Resource,
    TextContent,
    Tool,
)

# Import our JustiFi tools
from tools.justifi import (
    _get_access_token,
    create_payment,
    list_payments,
    refund_payment,
    retrieve_payment,
)

# Initialize the MCP server
server: Server = Server("justifi-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available JustiFi payment tools."""
    return [
        Tool(
            name="create_payment",
            description="Create a new payment in JustiFi",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_cents": {
                        "type": "integer",
                        "description": "Payment amount in cents (e.g., 1050 for $10.50)",
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (e.g., 'USD')",
                        "default": "USD",
                    },
                    "idempotency_key": {
                        "type": "string",
                        "description": "Unique key to prevent duplicate payments",
                    },
                    "payment_method_id": {
                        "type": "string",
                        "description": "Optional payment method ID",
                        "optional": True,
                    },
                },
                "required": ["amount_cents", "currency", "idempotency_key"],
            },
        ),
        Tool(
            name="retrieve_payment",
            description="Retrieve details of an existing payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": "The ID of the payment to retrieve",
                    }
                },
                "required": ["payment_id"],
            },
        ),
        Tool(
            name="list_payments",
            description="List payments with optional pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of payments to return (default: 25)",
                        "default": 25,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "after_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get payments after this cursor)",
                        "optional": True,
                    },
                    "before_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get payments before this cursor)",
                        "optional": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="refund_payment",
            description="Issue a refund for an existing payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": "The ID of the payment to refund",
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "Amount to refund in cents (optional for partial refunds)",
                        "optional": True,
                    },
                    "idempotency_key": {
                        "type": "string",
                        "description": "Unique key to prevent duplicate refunds",
                        "optional": True,
                    },
                },
                "required": ["payment_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for JustiFi operations."""
    try:
        if name == "create_payment":
            result = await create_payment(
                amount_cents=arguments["amount_cents"],
                currency=arguments["currency"],
                idempotency_key=arguments["idempotency_key"],
                payment_method_id=arguments.get("payment_method_id"),
            )
            return [
                TextContent(type="text", text=f"Payment created successfully: {result}")
            ]

        elif name == "retrieve_payment":
            result = await retrieve_payment(payment_id=arguments["payment_id"])
            return [TextContent(type="text", text=f"Payment details: {result}")]

        elif name == "list_payments":
            result = await list_payments(
                limit=arguments.get("limit", 25),
                after_cursor=arguments.get("after_cursor"),
                before_cursor=arguments.get("before_cursor"),
            )
            return [TextContent(type="text", text=f"Payments list: {result}")]

        elif name == "refund_payment":
            result = await refund_payment(
                payment_id=arguments["payment_id"],
                amount_cents=arguments.get("amount_cents"),
                idempotency_key=arguments.get("idempotency_key"),
            )
            return [TextContent(type="text", text=f"Refund processed: {result}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources (none for this server)."""
    return []


@server.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """List available prompts (none for this server)."""
    return []


async def main():
    """Run the MCP server using stdio transport."""
    # Load environment variables from .env file
    load_dotenv()

    # Validate required environment variables
    required_env_vars = ["JUSTIFI_CLIENT_ID", "JUSTIFI_CLIENT_SECRET"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return

    # Test JustiFi API connectivity
    try:
        await _get_access_token()
        print("✅ JustiFi API connection successful")
    except Exception as e:
        print(f"❌ JustiFi API connection failed: {e}")
        print("Please check your JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET")
        return

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
