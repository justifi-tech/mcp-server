"""FastMCP Server Implementation for JustiFi."""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from python.config import JustiFiConfig

from .dcr import handle_client_registration
from .oauth_metadata import (
    get_authorization_server_metadata,
    get_protected_resource_metadata,
)


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with all JustiFi tools."""
    mcp: FastMCP = FastMCP("JustiFi Payment Server")

    config = JustiFiConfig()

    # For stdio mode, credentials are required
    # For HTTP mode with OAuth, credentials are optional (bearer tokens used)
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        if not config.client_id or not config.client_secret:
            raise ValueError(
                "JustiFi client_id and client_secret must be configured for stdio mode"
            )

    if transport == "http":
        from .middleware.oauth import OAuthMiddleware

        mcp.add_middleware(OAuthMiddleware)

    register_tools(mcp, config)

    register_oauth_routes(mcp, config)

    register_health_check_route(mcp)

    return mcp


def register_oauth_routes(mcp: FastMCP, config: JustiFiConfig) -> None:
    """Register OAuth 2.0 discovery and registration endpoints.

    Registers:
    - /.well-known/oauth-protected-resource (RFC 9728)
    - /.well-known/oauth-authorization-server (RFC 8414)
    - /register (RFC 7591 - credential discovery)

    None of these endpoints require authentication.

    Args:
        mcp: FastMCP server instance
        config: JustiFi configuration with OAuth settings
    """

    @mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
    async def protected_resource_metadata_endpoint(request: Request) -> Response:
        """OAuth 2.0 Protected Resource Metadata endpoint (RFC 9728)."""
        metadata = get_protected_resource_metadata(config)
        return JSONResponse(metadata)

    @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def authorization_server_metadata_endpoint(request: Request) -> Response:
        """OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414)."""
        metadata = get_authorization_server_metadata(config)
        return JSONResponse(metadata)

    @mcp.custom_route("/register", methods=["POST"])
    async def client_registration_endpoint(request: Request) -> Response:
        """OAuth 2.0 Dynamic Client Registration endpoint (RFC 7591).

        Returns shared credentials for MCP client compatibility.
        Actual redirect_uri validation is performed by Auth0.
        """
        return await handle_client_registration(request, config)


def register_health_check_route(mcp: FastMCP) -> None:
    """Register health check endpoint for load balancer health checks.

    This endpoint does NOT require authentication and returns a simple
    "OK" response to indicate the server is running.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check_endpoint(request: Request) -> Response:
        """Health check endpoint for ALB/load balancer health checks."""
        return PlainTextResponse("OK")


def register_tools(mcp: FastMCP, config: JustiFiConfig) -> None:
    """Register all JustiFi tools with FastMCP server."""
    from .auto_register import auto_register_tools

    auto_register_tools(mcp, config)
