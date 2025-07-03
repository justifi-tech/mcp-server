"""
Framework Adapters for JustiFi Tools

This module provides adapters to integrate JustiFi tools with different
AI frameworks (MCP, LangChain, OpenAI Agent SDK, etc.).
"""

from .mcp import MCPAdapter

# Registry of available adapters
AVAILABLE_ADAPTERS = {
    "mcp": MCPAdapter,
}

__all__ = [
    "MCPAdapter",
    "AVAILABLE_ADAPTERS",
]
