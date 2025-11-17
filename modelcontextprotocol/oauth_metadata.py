"""OAuth 2.0 Protected Resource Metadata per RFC 9728.

This module implements the OAuth 2.0 Protected Resource Metadata endpoint
as specified in RFC 9728 (https://www.rfc-editor.org/rfc/rfc9728.html).

The endpoint provides information about:
- Authorization servers that can issue tokens for this resource
- OAuth scopes supported by this resource
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from python.config import JustiFiConfig


def get_protected_resource_metadata(config: JustiFiConfig) -> dict[str, list]:
    """Return OAuth 2.0 Protected Resource Metadata per RFC 9728.

    Args:
        config: JustiFi configuration containing Auth0 domain and OAuth scopes

    Returns:
        Dictionary containing:
        - authorization_servers: List of authorization server metadata
        - scopes_supported: List of OAuth scopes supported by this resource

    Example:
        >>> config = JustiFiConfig()
        >>> metadata = get_protected_resource_metadata(config)
        >>> print(metadata)
        {
            "authorization_servers": [
                {"issuer": "https://justifi.us.auth0.com"}
            ],
            "scopes_supported": ["read:payments", "write:payments"]
        }
    """
    return {
        "authorization_servers": [{"issuer": f"https://{config.auth0_domain}"}],
        "scopes_supported": config.oauth_scopes,
    }
