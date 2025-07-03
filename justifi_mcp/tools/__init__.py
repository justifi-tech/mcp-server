"""
JustiFi Tools - Framework-Agnostic Business Logic

This module contains pure business logic for JustiFi operations,
separated from any specific framework (MCP, LangChain, etc.).
"""

from .payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)

# Tool registry for framework adapters
AVAILABLE_TOOLS = {
    "retrieve_payout": retrieve_payout,
    "list_payouts": list_payouts,
    "get_payout_status": get_payout_status,
    "get_recent_payouts": get_recent_payouts,
}

# Tool metadata for framework adapters
TOOL_SCHEMAS = {
    "retrieve_payout": {
        "name": "retrieve_payout",
        "description": "Retrieve detailed information about a specific payout by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "payout_id": {
                    "type": "string",
                    "description": "The unique identifier for the payout (e.g., 'po_ABC123XYZ')",
                }
            },
            "required": ["payout_id"],
        },
    },
    "list_payouts": {
        "name": "list_payouts",
        "description": "List payouts with optional pagination using cursor-based pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of payouts to return (1-100, default: 25)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 25,
                },
                "after_cursor": {
                    "type": "string",
                    "description": "Cursor for pagination - returns results after this cursor",
                },
                "before_cursor": {
                    "type": "string",
                    "description": "Cursor for pagination - returns results before this cursor",
                },
            },
            "required": [],
        },
    },
    "get_payout_status": {
        "name": "get_payout_status",
        "description": "Get the current status of a payout (quick status check).",
        "parameters": {
            "type": "object",
            "properties": {
                "payout_id": {
                    "type": "string",
                    "description": "The unique identifier for the payout",
                }
            },
            "required": ["payout_id"],
        },
    },
    "get_recent_payouts": {
        "name": "get_recent_payouts",
        "description": "Get the most recent payouts (optimized for recency).",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent payouts to return (1-50, default: 10)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                }
            },
            "required": [],
        },
    },
}

__all__ = [
    "AVAILABLE_TOOLS",
    "TOOL_SCHEMAS",
    "retrieve_payout",
    "list_payouts",
    "get_payout_status",
    "get_recent_payouts",
]
