"""
Response Wrapper for JustiFi MCP Tools

Provides a wrapper that can optionally standardize responses from existing tools
without modifying the original tool implementations.
"""

from __future__ import annotations

import functools
import os
from typing import Any, Awaitable, Callable

from .response_formatter import standardize_response

# Configuration flag - can be set via environment variable
_STANDARDIZE_RESPONSES = os.getenv(
    "JUSTIFI_STANDARDIZE_RESPONSES", "false"
).lower() in ("true", "1", "yes", "on")


def set_standardization_enabled(enabled: bool) -> None:
    """Enable or disable response standardization globally."""
    global _STANDARDIZE_RESPONSES
    _STANDARDIZE_RESPONSES = enabled


def is_standardization_enabled() -> bool:
    """Check if response standardization is enabled."""
    return _STANDARDIZE_RESPONSES


def standardize_tool_response(tool_name: str) -> Callable:
    """
    Decorator to conditionally standardize tool responses.

    Args:
        tool_name: The name of the tool for metadata

    Returns:
        Decorator function
    """

    def decorator(
        func: Callable[..., Awaitable[dict[str, Any]]],
    ) -> Callable[..., Awaitable[dict[str, Any]]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = await func(*args, **kwargs)

            # If standardization is enabled, standardize the response
            if _STANDARDIZE_RESPONSES:
                return standardize_response(result, tool_name)

            # Otherwise return the original response
            return result

        return wrapper

    return decorator


async def maybe_standardize_response(
    response: dict[str, Any], tool_name: str
) -> dict[str, Any]:
    """
    Conditionally standardize a response based on global configuration.

    Args:
        response: The original tool response
        tool_name: The name of the tool that generated the response

    Returns:
        Either the original response or a standardized version
    """
    if _STANDARDIZE_RESPONSES:
        return standardize_response(response, tool_name)
    return response


# Tool-specific wrapper functions that can be used in the MCP server
async def wrap_retrieve_payout(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_payout with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_payout")


async def wrap_list_payouts(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_payouts with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_payouts")


async def wrap_get_recent_payouts(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap get_recent_payouts with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "get_recent_payouts")


async def wrap_get_payout_status(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap get_payout_status with optional standardization."""
    result = await original_func(*args, **kwargs)
    # get_payout_status returns a string, so we need to wrap it in a dict for standardization
    if _STANDARDIZE_RESPONSES:
        wrapped_result = {"data": result, "status": result}
        return standardize_response(wrapped_result, "get_payout_status")
    return result


async def wrap_retrieve_payment(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_payment with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_payment")


async def wrap_list_payments(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_payments with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_payments")


async def wrap_list_balance_transactions(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_balance_transactions with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_balance_transactions")


async def wrap_retrieve_balance_transaction(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_balance_transaction with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_balance_transaction")


async def wrap_list_disputes(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_disputes with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_disputes")


async def wrap_retrieve_dispute(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_dispute with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_dispute")


async def wrap_list_refunds(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_refunds with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_refunds")


async def wrap_retrieve_refund(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_refund with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_refund")


async def wrap_list_payment_refunds(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_payment_refunds with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_payment_refunds")


async def wrap_list_checkouts(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap list_checkouts with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "list_checkouts")


async def wrap_retrieve_checkout(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_checkout with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_checkout")


async def wrap_retrieve_payment_method(
    original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Wrap retrieve_payment_method with optional standardization."""
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, "retrieve_payment_method")


# Generic wrapper that can wrap any tool based on its name
TOOL_WRAPPERS = {
    "retrieve_payout": wrap_retrieve_payout,
    "list_payouts": wrap_list_payouts,
    "get_recent_payouts": wrap_get_recent_payouts,
    "get_payout_status": wrap_get_payout_status,
    "retrieve_payment": wrap_retrieve_payment,
    "list_payments": wrap_list_payments,
    "list_balance_transactions": wrap_list_balance_transactions,
    "retrieve_balance_transaction": wrap_retrieve_balance_transaction,
    "list_disputes": wrap_list_disputes,
    "retrieve_dispute": wrap_retrieve_dispute,
    "list_refunds": wrap_list_refunds,
    "retrieve_refund": wrap_retrieve_refund,
    "list_payment_refunds": wrap_list_payment_refunds,
    "list_checkouts": wrap_list_checkouts,
    "retrieve_checkout": wrap_retrieve_checkout,
    "retrieve_payment_method": wrap_retrieve_payment_method,
}


async def wrap_tool_call(
    tool_name: str, original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """
    Generic tool wrapper that can standardize any tool response.

    Args:
        tool_name: Name of the tool being called
        original_func: The original tool function
        *args, **kwargs: Arguments to pass to the tool

    Returns:
        Either the original response or a standardized version
    """
    wrapper = TOOL_WRAPPERS.get(tool_name)
    if wrapper:
        return await wrapper(original_func, *args, **kwargs)

    # Fallback for tools without specific wrappers
    result = await original_func(*args, **kwargs)
    return await maybe_standardize_response(result, tool_name)
