"""FastMCP Server Implementation for JustiFi."""

from fastmcp import FastMCP

from python.config import JustiFiConfig
from python.core import JustiFiClient


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with all JustiFi tools."""
    # Initialize FastMCP server
    mcp: FastMCP = FastMCP("JustiFi Payment Server")

    # Load configuration
    config = JustiFiConfig()

    # Ensure we have valid credentials
    client_id = config.client_id
    client_secret = config.client_secret
    if not client_id or not client_secret:
        raise ValueError("JustiFi client_id and client_secret must be configured")

    client = JustiFiClient(
        client_id=client_id,
        client_secret=client_secret,
    )

    # Register all JustiFi tools
    register_tools(mcp, client)

    return mcp


def register_tools(mcp: FastMCP, client: JustiFiClient) -> None:
    """Register all JustiFi tools with FastMCP server."""
    # Use automatic registration system
    from .auto_register import auto_register_tools

    auto_register_tools(mcp, client)


