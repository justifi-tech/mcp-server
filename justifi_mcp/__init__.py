"""JustiFi MCP Server - Payment Integration for AI-Assisted Development

A Model Context Protocol (MCP) server that provides AI agents with tools
to interact with the JustiFi payment API.
"""

__version__ = "2.0.0-dev"
__author__ = "JustiFi MCP Team"
__email__ = "support@justifi.ai"

# Export main components
from .core import JustiFiClient
from .payouts import list_payouts, retrieve_payout

__all__ = [
    "JustiFiClient",
    "retrieve_payout",
    "list_payouts",
]
