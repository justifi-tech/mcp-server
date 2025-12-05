"""FastMCP Server Implementation for JustiFi."""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from python.config import JustiFiConfig

from .dcr import handle_client_registration


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with all JustiFi tools."""
    config = JustiFiConfig()

    # For stdio mode, credentials are required
    # For HTTP mode with OAuth, credentials are optional (bearer tokens used)
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        if not config.client_id or not config.client_secret:
            raise ValueError(
                "JustiFi client_id and client_secret must be configured for stdio mode"
            )

    auth_provider = None
    if transport == "http":
        auth_provider = create_auth_provider(config)

    mcp: FastMCP = FastMCP("JustiFi Payment Server", auth=auth_provider)

    register_tools(mcp, config)

    register_oauth_routes(mcp, config)

    register_health_check_route(mcp)

    return mcp


def create_auth_provider(config: JustiFiConfig):
    """Create OAuth auth provider for HTTP transport.

    Uses FastMCP's built-in JWTVerifier with Auth0's JWKS endpoint
    for token validation, wrapped in RemoteAuthProvider for proper
    OAuth 2.0 Protected Resource Metadata (RFC 9728).

    Args:
        config: JustiFi configuration with OAuth settings

    Returns:
        RemoteAuthProvider configured for Auth0 JWT validation
    """
    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider
    from pydantic import AnyHttpUrl

    jwks_uri = f"{config.oauth_issuer.rstrip('/')}/.well-known/jwks.json"

    token_verifier = JWTVerifier(
        jwks_uri=jwks_uri,
        issuer=config.oauth_issuer,
        audience=config.oauth_audience,
        required_scopes=config.oauth_scopes if config.oauth_scopes else None,
    )

    if not config.mcp_server_url:
        raise ValueError(
            "MCP_SERVER_URL must be configured for HTTP transport with OAuth"
        )

    return RemoteAuthProvider(
        token_verifier=token_verifier,
        authorization_servers=[AnyHttpUrl(config.mcp_server_url)],
        base_url=config.mcp_server_url,
        resource_name="JustiFi MCP Server",
        resource_documentation=AnyHttpUrl("https://developer.justifi.ai"),
    )


def register_oauth_routes(mcp: FastMCP, config: JustiFiConfig) -> None:
    """Register OAuth 2.0 discovery and registration endpoints.

    Note: Protected resource metadata (RFC 9728) is automatically handled by
    FastMCP's RemoteAuthProvider. We add authorization server metadata here
    because MCP clients expect to find it at the MCP server URL.

    Registers:
    - /.well-known/oauth-authorization-server (RFC 8414 - points to Auth0)
    - /register (RFC 7591 - credential discovery for shared OAuth credentials)

    Args:
        mcp: FastMCP server instance
        config: JustiFi configuration with OAuth settings
    """
    from starlette.responses import JSONResponse

    def get_authorization_server_metadata() -> dict:
        """Build OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
        auth0_base = config.oauth_issuer.rstrip("/")

        metadata: dict = {
            "issuer": config.oauth_issuer,
            "authorization_endpoint": f"{auth0_base}/authorize",
            "token_endpoint": f"{auth0_base}/oauth/token",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
            ],
        }

        if config.mcp_server_url:
            mcp_base = config.mcp_server_url.rstrip("/")
            metadata["registration_endpoint"] = f"{mcp_base}/register"

        if config.oauth_scopes:
            metadata["scopes_supported"] = config.oauth_scopes

        return metadata

    @mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
    async def authorization_server_metadata_endpoint(request: Request) -> Response:
        """OAuth 2.0 Authorization Server Metadata endpoint (RFC 8414)."""
        return JSONResponse(get_authorization_server_metadata())

    @mcp.custom_route("/.well-known/oauth-authorization-server/mcp", methods=["GET"])
    async def authorization_server_metadata_mcp_endpoint(request: Request) -> Response:
        """OAuth 2.0 Authorization Server Metadata for /mcp path (RFC 8414)."""
        return JSONResponse(get_authorization_server_metadata())

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
