"""Automatic MCP tool registration system.

This module provides dynamic discovery and registration of all available JustiFi tools,
eliminating the need for manual tool registration boilerplate.
"""

import ast
import inspect
import logging
from collections.abc import Callable
from typing import Any, get_type_hints

from fastmcp import FastMCP

from python.core import JustiFiClient
from python.tools.response_wrapper import wrap_tool_call

logger = logging.getLogger(__name__)


def auto_register_tools(mcp: FastMCP, client: JustiFiClient) -> None:
    """Automatically register all available tools with MCP server.

    Args:
        mcp: FastMCP server instance
        client: JustiFi client instance
    """
    # Import tools package for discovery
    from python import tools

    # Discover available tools
    available_tools = discover_tools()

    logger.info(f"Auto-registering {len(available_tools)} tools")

    for tool_name in available_tools:
        try:
            tool_func = getattr(tools, tool_name)
            register_single_tool(mcp, client, tool_name, tool_func)
            logger.debug(f"Successfully registered tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {e}")
            # Continue registering other tools even if one fails
            continue


def discover_tools() -> list[str]:
    """Discover all available tool functions from the tools package.

    Returns:
        List of tool function names available for registration
    """
    from python import tools

    tool_functions = []

    # Get all exported functions from __all__ if available
    if hasattr(tools, "__all__"):
        # Filter out non-functions and utility functions
        for name in tools.__all__:
            if name not in ["standardize_response", "wrap_tool_call"]:
                obj = getattr(tools, name, None)
                if obj and inspect.iscoroutinefunction(obj):
                    tool_functions.append(name)
    else:
        # Fallback: inspect all public functions
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
    mcp: FastMCP, client: JustiFiClient, tool_name: str, tool_func: Callable
) -> None:
    """Register a single tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        client: JustiFi client instance
        tool_name: Name of the tool to register
        tool_func: Tool function to register
    """
    # Extract function metadata for MCP registration
    metadata = extract_tool_metadata(tool_func)

    # Create dynamic MCP tool function with preserved signature
    mcp_tool_wrapper = create_mcp_function(tool_name, tool_func, client, metadata)

    # Register with MCP
    mcp.tool(mcp_tool_wrapper)


def extract_original_signature(tool_func: Callable) -> inspect.Signature:
    """Extract original function signature, handling decorators.

    This function handles decorator chains by looking through __wrapped__ attributes
    and falls back to AST parsing if needed.
    """
    # Try to get original function through __wrapped__ chain
    original_func = tool_func
    while hasattr(original_func, "__wrapped__"):
        original_func = original_func.__wrapped__

    try:
        return inspect.signature(original_func)
    except (ValueError, TypeError):
        # Fallback: Parse signature from source code using AST
        return parse_signature_from_source(tool_func)


def parse_signature_from_source(func: Callable) -> inspect.Signature:
    """Parse function signature from source code using AST."""
    try:
        source = inspect.getsource(func)
        tree = ast.parse(source)
        func_def = None

        # Find the function definition in AST
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == func.__name__:
                func_def = node
                break

        if func_def:
            # Convert AST parameters to inspect.Parameter objects
            parameters = []
            for arg in func_def.args.args:
                param = inspect.Parameter(
                    arg.arg,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=arg.annotation.id
                    if arg.annotation
                    else inspect.Parameter.empty,
                )
                parameters.append(param)

            return inspect.Signature(parameters)
    except Exception:
        pass

    # Final fallback - create minimal signature
    return inspect.Signature(
        [
            inspect.Parameter("client", inspect.Parameter.POSITIONAL_OR_KEYWORD),
            inspect.Parameter("args", inspect.Parameter.VAR_POSITIONAL),
        ]
    )


def extract_tool_metadata(tool_func: Callable) -> dict[str, Any]:
    """Extract metadata from tool function for MCP registration.

    Args:
        tool_func: Tool function to extract metadata from

    Returns:
        Dictionary containing function metadata (signature, docstring, annotations)
    """
    try:
        # Extract original signature using improved method
        original_sig = extract_original_signature(tool_func)

        # Remove 'client' parameter for MCP interface
        filtered_params = []
        for name, param in original_sig.parameters.items():
            if name != "client":
                filtered_params.append(param)

        # Create new signature without client parameter
        new_sig = original_sig.replace(parameters=filtered_params)

        # Extract type annotations (excluding client)
        try:
            # Try to get type hints from original function
            original_func = tool_func
            while hasattr(original_func, "__wrapped__"):
                original_func = original_func.__wrapped__

            type_hints = get_type_hints(original_func)
            annotations = {
                name: hint for name, hint in type_hints.items() if name != "client"
            }
        except Exception:
            # Fallback to basic annotations from signature
            annotations = {}
            for param in filtered_params:
                if param.annotation != inspect.Parameter.empty:
                    annotations[param.name] = param.annotation

        return_annotation = original_sig.return_annotation
        if return_annotation == inspect.Signature.empty:
            return_annotation = dict[str, Any]

    except Exception as e:
        logger.warning(f"Failed to extract signature for {tool_func.__name__}: {e}")
        # Create minimal signature as fallback
        new_sig = None
        annotations = {}
        filtered_params = []
        return_annotation = dict[str, Any]

    # Extract docstring
    docstring = inspect.getdoc(tool_func) or f"Execute {tool_func.__name__} operation"

    return {
        "signature": new_sig,
        "annotations": annotations,
        "parameters": filtered_params,
        "docstring": docstring,
        "return_annotation": return_annotation,
    }


def create_mcp_function(
    tool_name: str, tool_func: Callable, client: JustiFiClient, metadata: dict[str, Any]
) -> Callable:
    """Create MCP function with correct signature and proper error handling.

    Args:
        tool_name: Name of the tool
        tool_func: Original tool function
        client: JustiFi client instance
        metadata: Extracted function metadata

    Returns:
        MCP-compatible async function
    """
    signature = metadata.get("signature")
    docstring = metadata["docstring"]
    return_annotation = metadata.get("return_annotation", dict[str, Any])

    if signature is not None:
        # Create function with preserved signature
        async def mcp_tool_wrapper(*args, **kwargs) -> dict[str, Any]:
            """Dynamically created MCP tool wrapper with preserved signature."""
            return await wrap_tool_call(tool_name, tool_func, client, *args, **kwargs)

        # Apply the preserved signature
        mcp_tool_wrapper.__signature__ = signature
    else:
        # Fallback for functions where signature extraction failed
        async def mcp_tool_wrapper(*args, **kwargs) -> dict[str, Any]:
            """Dynamically created MCP tool wrapper (fallback signature)."""
            return await wrap_tool_call(tool_name, tool_func, client, *args, **kwargs)

    # Set function metadata for MCP
    mcp_tool_wrapper.__name__ = tool_name
    mcp_tool_wrapper.__doc__ = docstring
    mcp_tool_wrapper.__annotations__ = {
        "return": return_annotation,
        **metadata.get("annotations", {}),
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
