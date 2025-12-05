"""
Response Wrapper for JustiFi MCP Tools

Provides a wrapper that standardizes responses from all tools.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from starlette.exceptions import HTTPException

from ..core import AuthenticationError
from .response_formatter import standardize_response


async def wrap_tool_call(
    tool_name: str, original_func: Callable, *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """
    Generic tool wrapper that standardizes any tool response.

    Handles AuthenticationError specially by raising HTTP 401 to trigger
    token refresh in MCP clients.

    Args:
        tool_name: Name of the tool being called
        original_func: The original tool function
        *args, **kwargs: Arguments to pass to the tool

    Returns:
        Standardized response

    Raises:
        HTTPException: With status 401 when authentication fails
    """
    try:
        # Special case for get_payout_status which returns a string
        if tool_name == "get_payout_status":
            result = await original_func(*args, **kwargs)
            # get_payout_status returns a string, wrap it in proper format
            wrapped_result = {"data": [{"status": result}]}
            return standardize_response(wrapped_result, tool_name)

        # All other tools follow the same pattern
        result = await original_func(*args, **kwargs)
        return standardize_response(result, tool_name)

    except AuthenticationError as e:
        # Convert to HTTP 401 so MCP clients know to refresh tokens
        error_code = e.error_code or "invalid_token"
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={
                "WWW-Authenticate": f'Bearer error="{error_code}", error_description="{str(e)}"'
            },
        ) from e
