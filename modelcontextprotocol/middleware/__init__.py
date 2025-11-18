"""Middleware components for JustiFi MCP Server.

This module contains middleware components used for request processing,
including OAuth authentication middleware.
"""

from .oauth import OAuthMiddleware

__all__ = ["OAuthMiddleware"]
