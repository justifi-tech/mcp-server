"""JustiFi Python Package - Core Tools and Utilities."""

from .config import JustiFiConfig
from .core import JustiFiClient
from .toolkit import JustiFiToolkit


def get_tool_schemas(toolkit: JustiFiToolkit):
    """Get tool schemas for OpenAI integration.

    Args:
        toolkit: JustiFiToolkit instance

    Returns:
        List of tool schema dictionaries compatible with OpenAI
    """
    return toolkit.get_langchain_schemas()


__all__ = ["JustiFiConfig", "JustiFiClient", "JustiFiToolkit", "get_tool_schemas"]
