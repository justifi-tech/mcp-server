"""
Standardized Response Formatter for JustiFi MCP Tools

Provides utilities to normalize API responses across all JustiFi tools into a
consistent format while preserving backward compatibility.
"""

from __future__ import annotations

from typing import Any


def standardize_response(
    response: dict[str, Any],
    tool_name: str,
    data_type_hint: str | None = None,
) -> dict[str, Any]:
    """
    Standardize a JustiFi API response into a consistent format.

    Args:
        response: The original API response from JustiFi
        tool_name: The name of the tool that generated the response
        data_type_hint: Optional hint about the data type (e.g., "payouts", "payments")

    Returns:
        Standardized response in the format:
        {
            "data": [...],           # Always contains the actual records
            "metadata": {
                "type": "payouts",     # Data type
                "count": 5,            # Number of records
                "tool": "list_payouts", # Source tool
                "original_format": "api" # Indicates original response format
            },
            "page_info": {...}       # Pagination info if applicable
        }
    """
    # Extract data type from tool name or hint
    data_type = _extract_data_type(tool_name, data_type_hint)

    # Handle different response formats
    if _is_custom_format(response, tool_name):
        # Handle custom formats like get_recent_payouts
        return _normalize_custom_response(response, tool_name, data_type)
    elif _is_api_format(response):
        # Handle standard JustiFi API format
        return _normalize_api_response(response, tool_name, data_type)
    elif _is_single_item_format(response):
        # Handle single item responses (retrieve_* operations)
        return _normalize_single_item_response(response, tool_name, data_type)
    else:
        # Fallback for unknown formats
        return _normalize_unknown_response(response, tool_name, data_type)


def _extract_data_type(tool_name: str, hint: str | None = None) -> str:
    """Extract the data type from tool name or hint."""
    if hint:
        return hint

    # Map tool names to data types
    type_mapping = {
        "list_payouts": "payouts",
        "get_recent_payouts": "payouts",
        "retrieve_payout": "payout",
        "get_payout_status": "payout_status",
        "list_payments": "payments",
        "retrieve_payment": "payment",
        "list_disputes": "disputes",
        "retrieve_dispute": "dispute",
        "list_refunds": "refunds",
        "retrieve_refund": "refund",
        "list_payment_refunds": "payment_refunds",
        "list_balance_transactions": "balance_transactions",
        "retrieve_balance_transaction": "balance_transaction",
        "list_checkouts": "checkouts",
        "retrieve_checkout": "checkout",
        "retrieve_payment_method": "payment_method",
        "create_payment_method_group": "payment_method_group",
        "list_payment_method_groups": "payment_method_groups",
        "retrieve_payment_method_group": "payment_method_group",
        "update_payment_method_group": "payment_method_group",
        "remove_payment_method_from_group": "payment_method_group",
        "list_proceeds": "proceeds",
        "retrieve_proceed": "proceed",
        "list_sub_accounts": "sub_accounts",
        "get_sub_account": "sub_account",
        "get_sub_account_payout_account": "sub_account_payout_account",
        "get_sub_account_settings": "sub_account_settings",
    }

    return type_mapping.get(tool_name, "unknown")


def _is_custom_format(response: dict[str, Any], tool_name: str) -> bool:
    """Check if response is in a custom format (like get_recent_payouts)."""
    # get_recent_payouts returns {"payouts": [...], "count": N, "limit": N}
    if tool_name == "get_recent_payouts":
        return "payouts" in response and "count" in response

    # Add other custom format checks here if needed
    return False


def _is_api_format(response: dict[str, Any]) -> bool:
    """Check if response is in standard JustiFi API format."""
    return "data" in response and isinstance(response["data"], list)


def _is_single_item_format(response: dict[str, Any]) -> bool:
    """Check if response is a single item (retrieve operations)."""
    return "data" in response and isinstance(response["data"], dict)


def _normalize_custom_response(
    response: dict[str, Any], tool_name: str, data_type: str
) -> dict[str, Any]:
    """Normalize custom format responses."""
    if tool_name == "get_recent_payouts":
        payouts_data = response.get("payouts", [])
        return {
            "data": payouts_data,
            "metadata": {
                "type": data_type,
                "count": len(payouts_data),
                "tool": tool_name,
                "original_format": "custom",
                "limit": response.get("limit"),
            },
            # No page_info for get_recent_payouts custom format
        }

    # Fallback for other custom formats
    return _normalize_unknown_response(response, tool_name, data_type)


def _normalize_api_response(
    response: dict[str, Any], tool_name: str, data_type: str
) -> dict[str, Any]:
    """Normalize standard JustiFi API list responses."""
    data = response.get("data", [])

    standardized = {
        "data": data,
        "metadata": {
            "type": data_type,
            "count": len(data) if isinstance(data, list) else 1,
            "tool": tool_name,
            "original_format": "api",
        },
    }

    # Preserve page_info if present
    if "page_info" in response:
        standardized["page_info"] = response["page_info"]

    return standardized


def _normalize_single_item_response(
    response: dict[str, Any], tool_name: str, data_type: str
) -> dict[str, Any]:
    """Normalize single item responses (retrieve operations)."""
    data_item = response.get("data", {})

    return {
        "data": (
            [data_item] if data_item else []
        ),  # Wrap single item in list for consistency
        "metadata": {
            "type": data_type,
            "count": 1 if data_item else 0,
            "tool": tool_name,
            "original_format": "api",
            "is_single_item": True,
        },
    }


def _normalize_unknown_response(
    response: dict[str, Any], tool_name: str, data_type: str
) -> dict[str, Any]:
    """Normalize responses with unknown format."""
    # Try to extract data intelligently
    possible_data = None
    count = 0

    # Look for common data fields
    for key in ["data", "results", "items"]:
        if key in response:
            possible_data = response[key]
            break

    # If no standard field found, use the entire response as data
    if possible_data is None:
        possible_data = response

    # Calculate count
    if isinstance(possible_data, list):
        count = len(possible_data)
    elif isinstance(possible_data, dict):
        count = 1
        possible_data = [possible_data]  # Wrap in list for consistency
    else:
        count = 0
        possible_data = []

    standardized = {
        "data": possible_data,
        "metadata": {
            "type": data_type,
            "count": count,
            "tool": tool_name,
            "original_format": "unknown",
            "warning": "Response format not recognized, data extraction was attempted",
        },
    }

    # Try to preserve page_info
    if "page_info" in response:
        standardized["page_info"] = response["page_info"]

    return standardized


def get_raw_data(standardized_response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract the raw data from a standardized response.

    Args:
        standardized_response: Response from standardize_response()

    Returns:
        List of data items (always a list, even for single items)
    """
    return standardized_response.get("data", [])


def is_single_item_response(standardized_response: dict[str, Any]) -> bool:
    """
    Check if the standardized response represents a single item.

    Args:
        standardized_response: Response from standardize_response()

    Returns:
        True if this was originally a single item response (retrieve operations)
    """
    metadata = standardized_response.get("metadata", {})
    return metadata.get("is_single_item", False)


def get_single_item(standardized_response: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract a single item from a standardized response if it represents one item.

    Args:
        standardized_response: Response from standardize_response()

    Returns:
        Single data item or None if not a single item response or empty
    """
    if not is_single_item_response(standardized_response):
        return None

    data = get_raw_data(standardized_response)
    return data[0] if data else None
