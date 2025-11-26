"""OAuth 2.0 Metadata Endpoints.

This module implements:
- RFC 9728: OAuth 2.0 Protected Resource Metadata
- RFC 8414: OAuth 2.0 Authorization Server Metadata

The MCP server acts as the discovery endpoint for OAuth, pointing clients to:
- Our /register endpoint for credential discovery
- Auth0 for actual authorization and token exchange
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from python.config import JustiFiConfig


def get_protected_resource_metadata(config: JustiFiConfig) -> dict:
    """Return OAuth 2.0 Protected Resource Metadata per RFC 9728.

    Points MCP clients to this server for OAuth discovery, which then
    directs them to Auth0 for actual authorization.

    Args:
        config: JustiFi configuration containing OAuth settings

    Returns:
        Dictionary containing:
        - resource: The protected resource identifier
        - authorization_servers: List pointing to this MCP server for discovery
        - scopes_supported: List of OAuth scopes supported by this resource
    """
    metadata: dict = {
        "authorization_servers": [{"issuer": config.mcp_server_url}],
        "scopes_supported": config.oauth_scopes,
    }

    if config.mcp_server_url:
        metadata["resource"] = config.mcp_server_url

    return metadata


def get_authorization_server_metadata(config: JustiFiConfig) -> dict:
    """Return OAuth 2.0 Authorization Server Metadata per RFC 8414.

    This metadata points clients to:
    - Our /register endpoint for credential discovery (shared credentials)
    - Auth0's endpoints for actual authorization and token exchange

    Args:
        config: JustiFi configuration containing OAuth settings

    Returns:
        Dictionary containing OAuth endpoints and capabilities
    """
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
