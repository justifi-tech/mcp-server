"""JustiFi MCP - Multi-Framework Payment Processing Toolkit

This package provides JustiFi payment processing tools that can be used with:
- Model Context Protocol (MCP) servers
- LangChain agents and tools
- OpenAI Assistant SDK
- Direct API integration

Example usage:
    from justifi_mcp import JustiFiToolkit

    # Create toolkit instance
    toolkit = JustiFiToolkit()

    # Use with LangChain
    langchain_tools = toolkit.get_langchain_tools()

    # Use with OpenAI
    openai_tools = toolkit.get_openai_tools()
"""

from python.config import JustiFiConfig
from python.core import JustiFiClient
from python.toolkit import JustiFiToolkit

# Import adapters for framework integration
try:
    from python.adapters.langchain import LangChainAdapter

    __all__ = [
        "JustiFiToolkit",
        "JustiFiConfig",
        "JustiFiClient",
        "LangChainAdapter",
        "TOOL_SCHEMAS",
    ]
except ImportError:
    __all__ = ["JustiFiToolkit", "JustiFiConfig", "JustiFiClient", "TOOL_SCHEMAS"]


# Create TOOL_SCHEMAS for OpenAI integration
# This provides a dictionary mapping tool names to their schemas
def _create_tool_schemas():
    """Create tool schemas dictionary for OpenAI integration."""
    toolkit = JustiFiToolkit()
    schemas = {}

    # Get all available tools and their schemas
    for tool_name in toolkit.get_enabled_tools():
        # Create a basic schema structure for each tool
        schemas[tool_name] = {
            "name": tool_name,
            "description": f"JustiFi tool: {tool_name}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    return schemas


TOOL_SCHEMAS = _create_tool_schemas()

__version__ = "2.0.0-dev"
__author__ = "JustiFi"
__description__ = "Multi-framework payment processing toolkit for AI agents"
