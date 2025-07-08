"""JustiFi MCP Configuration System

Simple whitelist-based configuration for tool selection and context management.
Enables secure, explicit tool selection with forward compatibility.
"""

from __future__ import annotations

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
        """Validate that credentials are provided."""
        field_name = info.field_name
        if not v:
            raise ValueError(
                f"{field_name} must be provided or set in "
                f"JUSTIFI_{field_name.upper()} environment variable"
            )
        return v

    @field_validator("enabled_tools")
    @classmethod
    def validate_enabled_tools(cls, v):
        """Validate enabled_tools field."""
        if isinstance(v, str):
            if v != "all":
                raise ValueError("enabled_tools string value must be 'all'")
            return v

        if isinstance(v, list):
            # Validate that all tool names are valid
            valid_tools = {
                # Payout tools
                "retrieve_payout",
                "list_payouts",
                "get_payout_status",
                "get_recent_payouts",
                # Payment tools
                "retrieve_payment",
                "list_payments",
                # Payment method tools
                "retrieve_payment_method",
                # Refund tools
                "list_refunds",
                "retrieve_refund",
                "list_payment_refunds",
                # Balance transaction tools
                "list_balance_transactions",
                "retrieve_balance_transaction",
                # Dispute tools
                "list_disputes",
                "retrieve_dispute",
                # Checkout tools
                "list_checkouts",
                "retrieve_checkout",
            }

            for tool in v:
                if tool not in valid_tools:
                    raise ValueError(
                        f"Unknown tool '{tool}'. Valid tools: {', '.join(sorted(valid_tools))}"
                    )
            return v

        raise ValueError("enabled_tools must be a list of tool names or 'all'")

    def get_available_tools(self) -> set[str]:
        """Get set of all available tool names."""
        return {
            # Payout tools
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "get_recent_payouts",
            # Payment tools
            "retrieve_payment",
            "list_payments",
            # Payment method tools
            "retrieve_payment_method",
            # Refund tools
            "list_refunds",
            "retrieve_refund",
            "list_payment_refunds",
            # Balance transaction tools
            "list_balance_transactions",
            "retrieve_balance_transaction",
            # Dispute tools
            "list_disputes",
            "retrieve_dispute",
            # Checkout tools
            "list_checkouts",
            "retrieve_checkout",
        }

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
