"""FastMCP Server Implementation for JustiFi."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from python.config import JustiFiConfig
from python.core import JustiFiClient

from .oauth_metadata import get_protected_resource_metadata


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

    # Register OAuth 2.0 Protected Resource Metadata endpoint (RFC 9728)
    register_oauth_metadata_route(mcp, config)

    return mcp


def register_oauth_metadata_route(mcp: FastMCP, config: JustiFiConfig) -> None:
    """Register OAuth 2.0 Protected Resource Metadata endpoint per RFC 9728.

    This endpoint does NOT require authentication and provides metadata about
    the OAuth authorization servers and scopes supported by this resource.

    Args:
        mcp: FastMCP server instance
        config: JustiFi configuration with OAuth settings
    """

    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def oauth_metadata_endpoint(request: Request) -> Response:
        """OAuth 2.0 Protected Resource Metadata endpoint (RFC 9728)."""
        metadata = get_protected_resource_metadata(config)
        return JSONResponse(metadata)


def register_tools(mcp: FastMCP, client: JustiFiClient) -> None:
    """Register all JustiFi tools with FastMCP server."""
    # Use automatic registration system
    from .auto_register import auto_register_tools

    auto_register_tools(mcp, client)
