"""OAuth 2.0 Dynamic Client Registration (Credential Discovery).

This module implements a minimal DCR endpoint per RFC 7591 that returns
shared credentials for known MCP clients. It's not true registration -
it's credential discovery disguised as DCR for MCP client compatibility.

Security is enforced by Auth0's redirect_uri allowlist, not by this endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from python.config import JustiFiConfig


async def handle_client_registration(
    request: Request, config: JustiFiConfig
) -> Response:
    """Handle RFC 7591 Dynamic Client Registration requests.

    This endpoint returns shared OAuth credentials to MCP clients.
    It does not actually register anything - Auth0 validates redirect_uris
    during the authorization flow.

    Args:
        request: The incoming HTTP request
        config: JustiFi configuration with shared OAuth credentials

    Returns:
        RFC 7591 compliant response with client credentials
    """
    if not config.oauth_client_id or not config.oauth_client_secret:
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_error",
                "error_description": "OAuth client credentials not configured",
            },
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    client_name = body.get("client_name", "MCP Client")
    redirect_uris = body.get("redirect_uris", [])

    return JSONResponse(
        status_code=201,
        content={
            "client_id": config.oauth_client_id,
            "client_secret": config.oauth_client_secret,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "token_endpoint_auth_method": "client_secret_post",
        },
    )
