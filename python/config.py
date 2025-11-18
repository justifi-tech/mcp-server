"""JustiFi MCP Configuration System

Simple whitelist-based configuration for tool selection and context management.
Enables secure, explicit tool selection with forward compatibility.
"""

from __future__ import annotations

import inspect
import os

from pydantic import BaseModel, Field, field_validator


class ContextConfig(BaseModel):
    """Global context configuration."""

    environment: str = Field(default="sandbox")
    """JustiFi environment: 'sandbox' or 'production'."""

    account_id: str | None = None
    """JustiFi account ID for multi-tenant setups."""

    timeout: int = Field(default=30, ge=5, le=300)
    """Default request timeout in seconds (5-300)."""

    rate_limit: str = Field(default="standard")
    """Default rate limiting tier: 'standard', 'premium', or 'unlimited'."""

    base_url: str | None = None
    """Override JustiFi API base URL."""

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        if v not in ["sandbox", "production"]:
            raise ValueError("environment must be 'sandbox' or 'production'")
        return v

    @field_validator("rate_limit")
    @classmethod
    def validate_rate_limit(cls, v):
        """Validate rate limit tier."""
        if v not in ["standard", "premium", "unlimited"]:
            raise ValueError("rate_limit must be 'standard', 'premium', or 'unlimited'")
        return v


class JustiFiConfig(BaseModel):
    """Complete JustiFi toolkit configuration with whitelist-based tool selection."""

    # Authentication
    client_id: str | None = None
    """JustiFi client ID (or from JUSTIFI_CLIENT_ID env var)."""

    client_secret: str | None = None
    """JustiFi client secret (or from JUSTIFI_CLIENT_SECRET env var)."""

    # OAuth 2.1 Configuration (optional)
    auth0_domain: str = Field(default="justifi.us.auth0.com")
    """Auth0 domain for OAuth 2.1 (or from JUSTIFI_AUTH0_DOMAIN env var)."""

    auth0_audience: str = Field(default="https://api.justifi.ai")
    """Auth0 audience for OAuth 2.1 (or from JUSTIFI_AUTH0_AUDIENCE env var)."""

    oauth_scopes: list[str] = Field(default_factory=list)
    """OAuth scopes supported by this resource (or from JUSTIFI_OAUTH_SCOPES env var, comma-separated)."""

    # Tool selection (whitelist approach)
    enabled_tools: list[str] | str = Field(default=[])
    """List of enabled tool names, or 'all' to enable all tools. Default: [] (no tools enabled - secure by default)."""

    # Global context
    context: ContextConfig = Field(default_factory=ContextConfig)
    """Global context and environment settings."""

    def __init__(self, **data):
        """Initialize configuration with environment variable fallbacks."""
        # Load from environment if not provided
        if "client_id" not in data or not data["client_id"]:
            data["client_id"] = os.getenv("JUSTIFI_CLIENT_ID")

        if "client_secret" not in data or not data["client_secret"]:
            data["client_secret"] = os.getenv("JUSTIFI_CLIENT_SECRET")

        # Load OAuth 2.1 configuration from environment
        if "auth0_domain" not in data:
            env_domain = os.getenv("JUSTIFI_AUTH0_DOMAIN")
            if env_domain:
                data["auth0_domain"] = env_domain

        if "auth0_audience" not in data:
            env_audience = os.getenv("JUSTIFI_AUTH0_AUDIENCE")
            if env_audience:
                data["auth0_audience"] = env_audience

        if "oauth_scopes" not in data:
            env_scopes = os.getenv("JUSTIFI_OAUTH_SCOPES")
            if env_scopes:
                data["oauth_scopes"] = [
                    s.strip() for s in env_scopes.split(",") if s.strip()
                ]

        # Handle context configuration
        if "context" in data and data["context"] is None:
            # Convert None to empty dict so Pydantic can create default ContextConfig
            data["context"] = {}

        # Load base URL from environment if not in context
        if "context" in data and isinstance(data["context"], dict):
            if "base_url" not in data["context"] or not data["context"]["base_url"]:
                data["context"]["base_url"] = os.getenv("JUSTIFI_BASE_URL")
        elif "context" not in data:
            data["context"] = {"base_url": os.getenv("JUSTIFI_BASE_URL")}

        super().__init__(**data)

    @field_validator("client_id", "client_secret")
    @classmethod
    def validate_credentials(cls, v, info):
        """Validate that credentials are provided for stdio mode.

        For HTTP mode with OAuth, credentials are optional (bearer tokens used instead).
        """
        # Allow None - validation happens at client creation time
        return v

    def _discover_available_tools(self) -> set[str]:
        """Auto-discover available tools from python.tools module.

        Returns:
            Set of available tool names found in the tools module
        """
        from . import tools

        discovered_tools = set()
        for name in dir(tools):
            if not name.startswith("_") and name not in [
                "standardize_response",
                "wrap_tool_call",
            ]:
                obj = getattr(tools, name)
                if inspect.iscoroutinefunction(obj):
                    discovered_tools.add(name)

        return discovered_tools

    @field_validator("enabled_tools")
    @classmethod
    def validate_enabled_tools(cls, v):
        """Validate enabled_tools field."""
        if isinstance(v, str):
            if v != "all":
                raise ValueError("enabled_tools string value must be 'all'")
            return v

        if isinstance(v, list):
            # Create a temporary instance to access the discovery method
            temp_instance = cls.__new__(cls)
            temp_instance.__dict__.update(
                {
                    "client_id": "temp",
                    "client_secret": "temp",
                    "enabled_tools": [],
                    "context": None,
                }
            )
            valid_tools = temp_instance._discover_available_tools()

            for tool in v:
                if tool not in valid_tools:
                    raise ValueError(
                        f"Unknown tool '{tool}'. Valid tools: {', '.join(sorted(valid_tools))}"
                    )
            return v

        raise ValueError("enabled_tools must be a list of tool names or 'all'")

    def get_available_tools(self) -> set[str]:
        """Get set of all available tool names."""
        return self._discover_available_tools()

    def get_enabled_tools(self) -> set[str]:
        """Get set of enabled tool names based on configuration."""
        if self.enabled_tools == "all":
            return self.get_available_tools()

        if isinstance(self.enabled_tools, list):
            return set(self.enabled_tools)

        # Fallback to empty set (no tools enabled)
        return set()

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a specific tool is enabled."""
        return tool_name in self.get_enabled_tools()

    def get_effective_timeout(self, tool_name: str) -> int:
        """Get effective timeout for a tool (uses global timeout)."""
        return self.context.timeout

    def get_effective_base_url(self) -> str:
        """Get effective base URL for API calls."""
        return self.context.base_url or "https://api.justifi.ai"
