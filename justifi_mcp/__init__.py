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
    __all__ = ["JustiFiToolkit", "JustiFiConfig", "JustiFiClient", "LangChainAdapter"]
except ImportError:
    __all__ = ["JustiFiToolkit", "JustiFiConfig", "JustiFiClient"]

__version__ = "2.0.0-dev"
__author__ = "JustiFi"
__description__ = "Multi-framework payment processing toolkit for AI agents"
