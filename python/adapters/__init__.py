"""
Framework Adapters for JustiFi Tools

This module provides adapters for different AI frameworks, enabling
the same business logic to work across LangChain and other frameworks.
"""

from .langchain import LangChainAdapter

# Adapter registry for dynamic loading
AVAILABLE_ADAPTERS = {
    "langchain": LangChainAdapter,
}

__all__ = [
    "LangChainAdapter",
    "AVAILABLE_ADAPTERS",
]
