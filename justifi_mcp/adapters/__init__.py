"""
Framework Adapters for JustiFi Tools

This module provides adapters for different AI frameworks, enabling
the same business logic to work across MCP, LangChain, OpenAI, and more.
"""

from .langchain import LangChainAdapter
from .mcp import MCPAdapter

# Adapter registry for dynamic loading
AVAILABLE_ADAPTERS = {
    "mcp": MCPAdapter,
    "langchain": LangChainAdapter,
    # Future adapters:
    # "openai": OpenAIAdapter,
    # "crewai": CrewAIAdapter,
}

__all__ = [
    "MCPAdapter",
    "LangChainAdapter",
    "AVAILABLE_ADAPTERS",
]
