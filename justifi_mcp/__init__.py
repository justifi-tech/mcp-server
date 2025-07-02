"""JustiFi MCP Server - Payment Integration for AI-Assisted Development

A Model Context Protocol (MCP) server that provides AI agents with tools
to interact with the JustiFi payment API.
"""

__version__ = "2.0.0-dev"
__author__ = "JustiFi MCP Team"
__email__ = "support@justifi.ai"

# Export main components
from .config import ContextConfig, JustiFiConfig, PayoutToolsConfig, ToolConfig
from .core import JustiFiClient
from .payouts import (
    get_payout_status,
    get_recent_payouts,
    list_payouts,
    retrieve_payout,
)
from .toolkit import JustiFiToolkit

__all__ = [
    # Main toolkit interface
    "JustiFiToolkit",
    # Configuration system
    "JustiFiConfig",
    "ToolConfig",
    "PayoutToolsConfig",
    "ContextConfig",
    # Core client
    "JustiFiClient",
    # Individual tools
    "retrieve_payout",
    "list_payouts",
    "get_payout_status",
    "get_recent_payouts",
]
