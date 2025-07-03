"""JustiFi MCP Server - Payment Integration for AI-Assisted Development

A Model Context Protocol (MCP) server that provides AI agents with tools
to interact with the JustiFi payment API.

Now with multi-framework support for MCP, LangChain, OpenAI Agent SDK, and more.
"""

__version__ = "2.0.0-dev"
__author__ = "JustiFi MCP Team"
__email__ = "support@justifi.ai"

# Export main components
# Framework adapters (for advanced usage)
from .adapters.langchain import LangChainAdapter
from .adapters.mcp import MCPAdapter
from .config import ContextConfig, JustiFiConfig
from .core import (
    APIError,
    AuthenticationError,
    JustiFiClient,
    JustiFiError,
    RateLimitError,
    ValidationError,
)
from .toolkit import JustiFiToolkit
from .tools.payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)

__all__ = [
    # Main toolkit interface (recommended)
    "JustiFiToolkit",
    # Configuration system
    "JustiFiConfig",
    "ContextConfig",
    # Core client
    "JustiFiClient",
    # Error classes
    "JustiFiError",
    "AuthenticationError",
    "ValidationError",
    "APIError",
    "RateLimitError",
    # Individual tools (for direct usage)
    "retrieve_payout",
    "list_payouts",
    "get_payout_status",
    "get_recent_payouts",
    # Framework adapters (advanced)
    "MCPAdapter",
    "LangChainAdapter",
]
