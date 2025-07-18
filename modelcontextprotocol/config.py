"""FastMCP Configuration for JustiFi MCP Server."""

import os
from typing import Literal

from pydantic import BaseModel, Field

TransportType = Literal["stdio", "http", "sse"]


class MCPConfig(BaseModel):
    """Configuration for FastMCP transport and server options."""

    transport: TransportType = Field(
        default="stdio", description="Transport type for MCP communication"
    )

    host: str = Field(
        default="127.0.0.1", description="Host address for HTTP/SSE transport"
    )

    port: int = Field(default=3000, description="Port for HTTP/SSE transport")

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        transport_str = os.getenv("MCP_TRANSPORT", "stdio")
        # Ensure transport is a valid TransportType
        transport: TransportType = (
            transport_str if transport_str in ["stdio", "http", "sse"] else "stdio"
        )

        return cls(
            transport=transport,
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "3000")),
        )
