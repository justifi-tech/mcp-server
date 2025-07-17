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
        "get_tool_schemas",
    ]
except ImportError:
    __all__ = ["JustiFiToolkit", "JustiFiConfig", "JustiFiClient", "get_tool_schemas"]


# Lazy-loading function for tool schemas - fixes import-time validation issue
def get_tool_schemas(toolkit_instance=None):
    """Get tool schemas dictionary for OpenAI integration.

    This function creates tool schemas on-demand, avoiding import-time validation
    issues when credentials are not available.

    Args:
        toolkit_instance: Optional pre-configured JustiFiToolkit instance.
                         If None, creates a minimal instance with dummy credentials.

    Returns:
        dict: Mapping of tool names to their OpenAI-compatible schemas

    Example:
        # Basic usage (uses dummy credentials for schema generation)
        schemas = get_tool_schemas()

        # With existing toolkit instance
        toolkit = JustiFiToolkit(client_id="real_id", client_secret="real_secret")
        schemas = get_tool_schemas(toolkit)
    """
    if toolkit_instance is None:
        # Create minimal toolkit instance with dummy credentials for schema generation
        # This avoids import-time validation while still generating correct schemas
        toolkit_instance = JustiFiToolkit(
            client_id="dummy_for_schema",
            client_secret="dummy_for_schema",
            enabled_tools="all",
        )

    schemas = {}

    # Get all available tools and their schemas
    for tool_name in toolkit_instance.get_enabled_tools():
        # Create a basic schema structure for each tool
        schemas[tool_name] = {
            "name": tool_name,
            "description": f"JustiFi tool: {tool_name}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    return schemas


try:
    from ._version import version as __version__
except ImportError:
    # Fallback to setuptools_scm if _version.py doesn't exist
    try:
        import os

        import setuptools_scm

        # Get the root directory (where pyproject.toml is)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        __version__ = setuptools_scm.get_version(root=root_dir)
    except (ImportError, Exception):
        __version__ = "0.0.0"
__author__ = "JustiFi"
__description__ = "Multi-framework payment processing toolkit for AI agents"
