"""
Full Integration Tests for All JustiFi Tools

Comprehensive tests that verify all tools work correctly through:
1. MCP server integration and registration
2. LangChain adapter integration and schema generation

This provides essential validation that all tools are properly
integrated across the supported interfaces.
"""

import pytest

from modelcontextprotocol.auto_register import discover_tools
from modelcontextprotocol.server import create_mcp_server
from python.config import JustiFiConfig


class TestMCPServerIntegration:
    """Test all tools through MCP server integration."""

    def test_mcp_server_complete_integration(self):
        """Test that MCP server successfully integrates all tools including new terminal tools."""
        # Test server creation
        server = create_mcp_server()
        assert server is not None

        # Test auto-discovery finds expected tool count
        tools = discover_tools()
        assert len(tools) >= 32, f"Expected at least 32 tools, found {len(tools)}"

        # Verify we have tools from all major categories
        # discover_tools returns a list of tool names, not functions
        tool_names = list(tools.keys()) if isinstance(tools, dict) else tools

        # Check for representative tools from each major category
        expected_categories = {
            "payment": ["list_payments", "retrieve_payment"],
            "payout": ["list_payouts", "retrieve_payout"],
            "terminal": ["list_terminals", "retrieve_terminal", "update_terminal"],
            "dispute": ["list_disputes", "retrieve_dispute"],
            "checkout": ["list_checkouts", "retrieve_checkout"],
            "refund": ["list_refunds", "retrieve_refund"],
        }

        for category, expected_tools in expected_categories.items():
            category_found = any(
                any(expected in str(tool_name) for expected in expected_tools)
                for tool_name in tool_names
            )
            assert category_found, f"Missing tools from {category} category"

        # Specifically verify terminal tools are included (our new addition)
        terminal_tools = [name for name in tool_names if "terminal" in str(name)]
        assert len(terminal_tools) >= 5, (
            f"Expected at least 5 terminal tools, found {len(terminal_tools)}"
        )


class TestLangChainAdapterIntegration:
    """Test all tools through LangChain adapter integration."""

    @pytest.fixture
    def test_config(self):
        """Create test config with dummy credentials."""
        return JustiFiConfig(
            client_id="test_client_id", client_secret="test_client_secret"
        )

    def test_langchain_adapter_complete_integration(self, test_config):
        """Test that LangChain adapter successfully integrates all tools including new terminal tools."""
        # Import here to handle optional dependency gracefully
        pytest.importorskip("langchain_core", reason="LangChain not installed")

        from python.adapters.langchain import LangChainAdapter

        # Test adapter creation and tool retrieval
        adapter = LangChainAdapter(test_config)
        tools = adapter.get_langchain_tools()

        # Should have at least 32 tools
        assert len(tools) >= 32, f"Expected at least 32 tools, found {len(tools)}"

        # Get all tool names
        tool_names = {tool.name for tool in tools}

        # Check for tools from each major category including new terminal tools
        required_tools = {
            "list_payments",
            "retrieve_payment",  # Payment tools
            "list_payouts",
            "retrieve_payout",  # Payout tools
            "list_terminals",
            "retrieve_terminal",  # Terminal tools (new)
            "list_disputes",
            "retrieve_dispute",  # Dispute tools
            "list_checkouts",
            "retrieve_checkout",  # Checkout tools
        }

        missing_tools = required_tools - tool_names
        assert not missing_tools, f"Missing required tools: {missing_tools}"

        # Verify each tool has proper LangChain structure
        sample_tool = next(tool for tool in tools if tool.name == "list_terminals")
        assert hasattr(sample_tool, "name")
        assert hasattr(sample_tool, "description")
        assert hasattr(sample_tool, "args_schema")
        assert sample_tool.description  # Should not be empty
        assert sample_tool.args_schema is not None  # Should have schema

        # Specifically verify terminal tools are properly integrated
        terminal_tools = [tool.name for tool in tools if "terminal" in tool.name]
        expected_terminal_tools = {
            "list_terminals",
            "retrieve_terminal",
            "update_terminal",
            "get_terminal_status",
            "identify_terminal",
        }
        found_terminal_tools = set(terminal_tools)

        assert expected_terminal_tools.issubset(found_terminal_tools), (
            f"Missing terminal tools: {expected_terminal_tools - found_terminal_tools}"
        )
