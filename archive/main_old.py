#!/usr/bin/env python3
"""JustiFi MCP Server

A Model Context Protocol server that provides tools for interacting with the JustiFi payments API.
Supports OAuth2 Client-Credentials authentication with token caching.
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

# Import our JustiFi tools
from tools.justifi import (
    _get_access_token,
    # Payment tools
    create_payment,
    # Payment method tools
    create_payment_method,
    # Balance tools
    list_balance_transactions,
    list_payments,
    list_payouts,
    refund_payment,
    retrieve_payment,
    retrieve_payment_method,
    # Payout tools
    retrieve_payout,
)

# Initialize the MCP server
server: Server = Server("justifi-mcp-server")

# Tool dispatch dictionary for scalable tool management
TOOL_DISPATCH = {
    "create_payment": create_payment,
    "retrieve_payment": retrieve_payment,
    "list_payments": list_payments,
    "refund_payment": refund_payment,
    "create_payment_method": create_payment_method,
    "retrieve_payment_method": retrieve_payment_method,
    "retrieve_payout": retrieve_payout,
    "list_payouts": list_payouts,
    "list_balance_transactions": list_balance_transactions,
}


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available JustiFi payment tools."""
    return [
        # Payment tools
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
        # Payment method tools
        Tool(
            name="create_payment_method",
            description="Create a new payment method (tokenized card)",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_number": {
                        "type": "string",
                        "description": "Credit card number (will be tokenized)",
                    },
                    "card_exp_month": {
                        "type": "string",
                        "description": "Card expiration month (MM)",
                    },
                    "card_exp_year": {
                        "type": "string",
                        "description": "Card expiration year (YYYY)",
                    },
                    "card_cvv": {
                        "type": "string",
                        "description": "Card CVV/CVC code",
                    },
                    "card_name": {
                        "type": "string",
                        "description": "Cardholder name",
                        "optional": True,
                    },
                    "address_line1": {
                        "type": "string",
                        "description": "Billing address line 1",
                        "optional": True,
                    },
                    "address_city": {
                        "type": "string",
                        "description": "Billing address city",
                        "optional": True,
                    },
                    "address_state": {
                        "type": "string",
                        "description": "Billing address state",
                        "optional": True,
                    },
                    "address_postal_code": {
                        "type": "string",
                        "description": "Billing address postal code",
                        "optional": True,
                    },
                    "address_country": {
                        "type": "string",
                        "description": "Billing address country",
                        "optional": True,
                    },
                },
                "required": [
                    "card_number",
                    "card_exp_month",
                    "card_exp_year",
                    "card_cvv",
                ],
            },
        ),
        Tool(
            name="retrieve_payment_method",
            description="Retrieve details of a payment method by token",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_method_token": {
                        "type": "string",
                        "description": "The token of the payment method to retrieve",
                    }
                },
                "required": ["payment_method_token"],
            },
        ),
        # Payout tools
        Tool(
            name="retrieve_payout",
            description="Retrieve details of a specific payout",
            inputSchema={
                "type": "object",
                "properties": {
                    "payout_id": {
                        "type": "string",
                        "description": "The ID of the payout to retrieve",
                    }
                },
                "required": ["payout_id"],
            },
        ),
        Tool(
            name="list_payouts",
            description="List payouts with optional pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of payouts to return (default: 25)",
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
        # Balance tools
        Tool(
            name="list_balance_transactions",
            description="List balance transactions (fund movements)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of transactions to return (default: 25)",
                        "default": 25,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "after_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get transactions after this cursor)",
                        "optional": True,
                    },
                    "before_cursor": {
                        "type": "string",
                        "description": "Cursor for pagination (get transactions before this cursor)",
                        "optional": True,
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for JustiFi operations using dispatch pattern."""
    try:
        # Check if tool exists in our dispatch table
        if name not in TOOL_DISPATCH:
            raise ValueError(f"Unknown tool: {name}")

        # Get the tool function
        tool_func = TOOL_DISPATCH[name]

        # Call the tool function with arguments
        result = await tool_func(**arguments)

        # Format the response
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

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


async def health_check():
    """Health check for container monitoring."""
    try:
        # Load environment variables
        load_dotenv()

        # Check required environment variables
        required_vars = [
            "JUSTIFI_CLIENT_ID",
            "JUSTIFI_CLIENT_SECRET",
            "JUSTIFI_BASE_URL",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            print(
                f"❌ Missing required environment variables: {', '.join(missing_vars)}"
            )
            return False

        # Test API connectivity
        await _get_access_token()
        print("✅ JustiFi API connection successful")
        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def main():
    """Main entry point for the MCP server."""
    # Load environment variables
    load_dotenv()

    # Check if this is a health check
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        success = await health_check()
        sys.exit(0 if success else 1)

    # Perform startup health check
    try:
        await health_check()
    except Exception as e:
        print(f"❌ Startup health check failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Start the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
