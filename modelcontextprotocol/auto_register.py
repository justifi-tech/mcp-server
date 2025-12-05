"""Automatic MCP tool registration system.

This module provides dynamic discovery and registration of all available JustiFi tools,
eliminating the need for manual tool registration boilerplate.
"""

import inspect
import logging
from collections.abc import Callable
from typing import Any, get_type_hints

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from mcp.server.auth.middleware.auth_context import get_access_token

from python.config import JustiFiConfig
from python.core import JustiFiClient
from python.tools.response_wrapper import wrap_tool_call

logger = logging.getLogger(__name__)


def auto_register_tools(mcp: FastMCP, config: JustiFiConfig) -> None:
    """Automatically register all available tools with MCP server.

    Args:
        mcp: FastMCP server instance
        config: JustiFi configuration instance
    """
    from python import tools

    available_tools = discover_tools()

    logger.info(f"Auto-registering {len(available_tools)} tools")

    for tool_name in available_tools:
        try:
            tool_func = getattr(tools, tool_name)
            register_single_tool(mcp, config, tool_name, tool_func)
            logger.debug(f"Successfully registered tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {e}")
            continue


def discover_tools() -> list[str]:
    """Discover all available tool functions from the tools package.

    Returns:
        List of tool function names available for registration
    """
    from python import tools

    tool_functions = []

    if hasattr(tools, "__all__"):
        for name in tools.__all__:
            if name not in ["standardize_response", "wrap_tool_call"]:
                obj = getattr(tools, name, None)
                if obj and inspect.iscoroutinefunction(obj):
                    tool_functions.append(name)
    else:
        for name in dir(tools):
            if not name.startswith("_") and name not in [
                "standardize_response",
                "wrap_tool_call",
            ]:
                obj = getattr(tools, name)
                if inspect.iscoroutinefunction(obj):
                    tool_functions.append(name)

    logger.info(f"Discovered {len(tool_functions)} tool functions")
    return sorted(tool_functions)


def register_single_tool(
    mcp: FastMCP, config: JustiFiConfig, tool_name: str, tool_func: Callable
) -> None:
    """Register a single tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        config: JustiFi configuration instance
        tool_name: Name of the tool to register
        tool_func: Tool function to register
    """
    metadata = extract_tool_metadata(tool_func)

    mcp_tool_wrapper = create_mcp_function(tool_name, tool_func, config, metadata)

    mcp.tool(mcp_tool_wrapper)


def extract_original_signature(tool_func: Callable) -> inspect.Signature:
    """Extract original function signature from __wrapped__ attribute.

    Since decorators now properly preserve __wrapped__, we can directly access
    the original signature without complex AST parsing.
    """
    original_func = tool_func
    while hasattr(original_func, "__wrapped__"):
        original_func = original_func.__wrapped__

    return inspect.signature(original_func)


def extract_tool_metadata(tool_func: Callable) -> dict[str, Any]:
    """Extract metadata from tool function for MCP registration.

    Args:
        tool_func: Tool function to extract metadata from

    Returns:
        Dictionary containing function metadata (signature, docstring, annotations)
    """
    original_sig = extract_original_signature(tool_func)

    filtered_params = []
    for name, param in original_sig.parameters.items():
        if name != "client":
            filtered_params.append(param)

    new_sig = original_sig.replace(parameters=filtered_params)

    original_func = tool_func
    while hasattr(original_func, "__wrapped__"):
        original_func = original_func.__wrapped__

    try:
        type_hints = get_type_hints(original_func)
        annotations = {
            name: hint for name, hint in type_hints.items() if name != "client"
        }
    except Exception:
        annotations = {}
        for param in filtered_params:
            if param.annotation != inspect.Parameter.empty:
                annotations[param.name] = param.annotation

    return_annotation = original_sig.return_annotation
    if return_annotation == inspect.Signature.empty:
        return_annotation = dict[str, Any]

    docstring = inspect.getdoc(tool_func) or f"Execute {tool_func.__name__} operation"

    return {
        "signature": new_sig,
        "annotations": annotations,
        "parameters": filtered_params,
        "docstring": docstring,
        "return_annotation": return_annotation,
    }


def create_mcp_function(
    tool_name: str, tool_func: Callable, config: JustiFiConfig, metadata: dict[str, Any]
) -> Callable:
    """Create MCP function with correct signature and proper error handling.

    Args:
        tool_name: Name of the tool
        tool_func: Original tool function
        config: JustiFi configuration instance
        metadata: Extracted function metadata

    Returns:
        MCP-compatible async function
    """
    signature = metadata["signature"]
    docstring = metadata["docstring"]
    return_annotation = metadata["return_annotation"]

    async def mcp_tool_wrapper(*args, **kwargs) -> dict[str, Any]:
        """Dynamically created MCP tool wrapper with per-request client."""
        access_token = get_access_token()

        # Get HTTP headers - FastMCP normalizes header names to lowercase
        headers: dict[str, str] = get_http_headers()
        platform_account_id = headers.get("sub-account")

        if access_token and access_token.token:
            client = JustiFiClient(
                client_id=config.client_id or "",
                client_secret=config.client_secret or "",
                base_url=config.get_effective_base_url(),
                bearer_token=access_token.token,
                platform_account_id=platform_account_id,
            )
        else:
            client = JustiFiClient(
                client_id=config.client_id or "",
                client_secret=config.client_secret or "",
                base_url=config.get_effective_base_url(),
                platform_account_id=platform_account_id,
            )

        return await wrap_tool_call(tool_name, tool_func, client, *args, **kwargs)

    mcp_tool_wrapper.__signature__ = signature
    mcp_tool_wrapper.__name__ = tool_name
    mcp_tool_wrapper.__doc__ = docstring
    mcp_tool_wrapper.__annotations__ = {
        "return": return_annotation,
        **metadata["annotations"],
    }
    mcp_tool_wrapper.__qualname__ = tool_name

    return mcp_tool_wrapper


def get_registered_tool_count() -> int:
    """Get the count of tools that would be registered.

    Utility function for testing and validation.

    Returns:
        Number of tools that would be auto-registered
    """
    return len(discover_tools())
