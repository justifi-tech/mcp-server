"""JustiFi MCP Configuration System

Stripe-like configuration for tool selection and context management.
Enables environment-specific tool sets and flexible deployment options.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, field_validator


class ToolConfig(BaseModel):
    """Configuration for individual tools."""

    enabled: bool = True
    """Whether this tool is enabled."""

    timeout: int | None = None
    """Override timeout for this specific tool (seconds)."""

    rate_limit: str | None = None
    """Rate limiting tier: 'standard', 'premium', or 'unlimited'."""


class PayoutToolsConfig(BaseModel):
    """Configuration for payout-related tools."""

    retrieve: ToolConfig = Field(default_factory=ToolConfig)
    """Configuration for retrieve_payout tool."""

    list: ToolConfig = Field(default_factory=ToolConfig)
    """Configuration for list_payouts tool."""

    status: ToolConfig = Field(default_factory=ToolConfig)
    """Configuration for get_payout_status tool."""

    recent: ToolConfig = Field(default_factory=ToolConfig)
    """Configuration for get_recent_payouts tool."""


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
    """Complete JustiFi toolkit configuration."""

    # Authentication
    client_id: str | None = None
    """JustiFi client ID (or from JUSTIFI_CLIENT_ID env var)."""

    client_secret: str | None = None
    """JustiFi client secret (or from JUSTIFI_CLIENT_SECRET env var)."""

    # Tool configurations
    tools: PayoutToolsConfig = Field(default_factory=PayoutToolsConfig)
    """Configuration for all available tools."""

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
        """Validate that credentials are provided."""
        field_name = info.field_name
        if not v:
            raise ValueError(
                f"{field_name} must be provided or set in "
                f"JUSTIFI_{field_name.upper()} environment variable"
            )
        return v

    def get_enabled_tools(self) -> dict[str, ToolConfig]:
        """Get dictionary of enabled tools and their configurations."""
        enabled_tools = {}

        # Check each payout tool
        if self.tools.retrieve.enabled:
            enabled_tools["retrieve_payout"] = self.tools.retrieve
        if self.tools.list.enabled:
            enabled_tools["list_payouts"] = self.tools.list
        if self.tools.status.enabled:
            enabled_tools["get_payout_status"] = self.tools.status
        if self.tools.recent.enabled:
            enabled_tools["get_recent_payouts"] = self.tools.recent

        return enabled_tools

    def get_tool_config(self, tool_name: str) -> ToolConfig | None:
        """Get configuration for a specific tool."""
        tool_mapping = {
            "retrieve_payout": self.tools.retrieve,
            "list_payouts": self.tools.list,
            "get_payout_status": self.tools.status,
            "get_recent_payouts": self.tools.recent,
        }
        return tool_mapping.get(tool_name)

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a specific tool is enabled."""
        tool_config = self.get_tool_config(tool_name)
        return tool_config.enabled if tool_config else False

    def get_effective_timeout(self, tool_name: str) -> int:
        """Get effective timeout for a tool (tool-specific or global default)."""
        tool_config = self.get_tool_config(tool_name)
        if tool_config and tool_config.timeout:
            return tool_config.timeout
        return self.context.timeout

    def get_effective_base_url(self) -> str:
        """Get effective base URL for API calls."""
        return self.context.base_url or "https://api.justifi.ai/v1"


# Default configurations for common scenarios
DEFAULT_CONFIG = JustiFiConfig()

PRODUCTION_CONFIG = JustiFiConfig(
    context=ContextConfig(
        environment="production",
        timeout=15,  # Shorter timeout for production
        rate_limit="premium",
    )
)

SANDBOX_CONFIG = JustiFiConfig(
    context=ContextConfig(
        environment="sandbox",
        timeout=30,  # Longer timeout for testing
        rate_limit="standard",
    )
)

# Restrictive configuration (only read operations)
READ_ONLY_CONFIG = JustiFiConfig(
    tools=PayoutToolsConfig(
        retrieve=ToolConfig(enabled=True),
        list=ToolConfig(enabled=True),
        status=ToolConfig(enabled=True),
        recent=ToolConfig(enabled=False),  # Disable recent payouts
    )
)
