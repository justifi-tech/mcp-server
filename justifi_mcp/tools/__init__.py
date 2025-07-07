"""
JustiFi Tools - Framework-Agnostic Business Logic

This module contains pure business logic for JustiFi operations,
separated from any specific framework (MCP, LangChain, etc.).
"""

from .balances import (
    list_balance_transactions,
    retrieve_balance_transaction,
)
from .payment_methods import (
    retrieve_payment_method,
)
from .payments import (
    list_payments,
    retrieve_payment,
)
from .payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)
from .refunds import (
    list_payment_refunds,
    list_refunds,
    retrieve_refund,
)

# Tool registry for framework adapters
AVAILABLE_TOOLS = {
    # Payout tools
    "retrieve_payout": retrieve_payout,
    "list_payouts": list_payouts,
    "get_payout_status": get_payout_status,
    "get_recent_payouts": get_recent_payouts,
    # Payment tools
    "retrieve_payment": retrieve_payment,
    "list_payments": list_payments,
    # Payment method tools
    "retrieve_payment_method": retrieve_payment_method,
    # Refund tools
    "list_refunds": list_refunds,
    "retrieve_refund": retrieve_refund,
    "list_payment_refunds": list_payment_refunds,
    # Balance transaction tools
    "list_balance_transactions": list_balance_transactions,
    "retrieve_balance_transaction": retrieve_balance_transaction,
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
    "retrieve_payment": {
        "name": "retrieve_payment",
        "description": "Retrieve detailed information about a specific payment by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {
                    "type": "string",
                    "description": "The unique identifier for the payment (e.g., 'py_ABC123XYZ')",
                }
            },
            "required": ["payment_id"],
        },
    },
    "list_payments": {
        "name": "list_payments",
        "description": "List payments with optional pagination using cursor-based pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of payments to return (1-100, default: 25)",
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
    "retrieve_payment_method": {
        "name": "retrieve_payment_method",
        "description": "Retrieve detailed information about a specific payment method by token.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_method_token": {
                    "type": "string",
                    "description": "The unique token for the payment method (e.g., 'pm_ABC123XYZ')",
                }
            },
            "required": ["payment_method_token"],
        },
    },
    "list_refunds": {
        "name": "list_refunds",
        "description": "List all refunds with optional pagination using cursor-based pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of refunds to return (1-100, default: 25)",
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
    "retrieve_refund": {
        "name": "retrieve_refund",
        "description": "Retrieve detailed information about a specific refund by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "refund_id": {
                    "type": "string",
                    "description": "The unique identifier for the refund (e.g., 're_ABC123XYZ')",
                }
            },
            "required": ["refund_id"],
        },
    },
    "list_payment_refunds": {
        "name": "list_payment_refunds",
        "description": "List refunds for a specific payment by extracting them from the payment data.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {
                    "type": "string",
                    "description": "The unique identifier for the payment (e.g., 'py_ABC123XYZ')",
                }
            },
            "required": ["payment_id"],
        },
    },
    "list_balance_transactions": {
        "name": "list_balance_transactions",
        "description": "List balance transactions with optional pagination and filtering by payout.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of balance transactions to return (1-100, default: 25)",
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
                "payout_id": {
                    "type": "string",
                    "description": "Filter records which are part of the payout with the specified id (e.g., 'po_ABC123XYZ')",
                },
            },
            "required": [],
        },
    },
    "retrieve_balance_transaction": {
        "name": "retrieve_balance_transaction",
        "description": "Retrieve detailed information about a specific balance transaction by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "balance_transaction_id": {
                    "type": "string",
                    "description": "The unique identifier for the balance transaction (e.g., 'bt_ABC123XYZ')",
                }
            },
            "required": ["balance_transaction_id"],
        },
    },
}

__all__ = [
    "AVAILABLE_TOOLS",
    "TOOL_SCHEMAS",
    # Payout tools
    "retrieve_payout",
    "list_payouts",
    "get_payout_status",
    "get_recent_payouts",
    # Payment tools
    "retrieve_payment",
    "list_payments",
    # Payment method tools
    "retrieve_payment_method",
    # Refund tools
    "list_refunds",
    "retrieve_refund",
    "list_payment_refunds",
    # Balance transaction tools
    "list_balance_transactions",
    "retrieve_balance_transaction",
]
