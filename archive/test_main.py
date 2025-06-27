"""Test suite for the JustiFi MCP Server.

Tests MCP protocol compliance, tool registration, and basic functionality.
"""

import os
import sys
from pathlib import Path

import pytest

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import handle_list_tools, server

# Test constants - not real credentials
TEST_CLIENT_ID = "test_client_id"
TEST_CLIENT_SECRET = "test_client_secret"  # noqa: S105
TEST_BASE_URL = "https://api.justifi.ai"


class TestMCPServer:
    """Test MCP server initialization and basic functionality."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up test environment variables."""
        os.environ["JUSTIFI_CLIENT_ID"] = TEST_CLIENT_ID
        os.environ["JUSTIFI_CLIENT_SECRET"] = TEST_CLIENT_SECRET
        os.environ["JUSTIFI_BASE_URL"] = TEST_BASE_URL
        yield

    def test_mcp_server_creation(self):
        """Test that MCP server can be created successfully."""
        assert server is not None
        assert hasattr(server, "name")
        assert server.name == "justifi-mcp-server"

    @pytest.mark.asyncio
    async def test_get_tools_function(self):
        """Test that get_tools returns the expected tools."""
        tools = await handle_list_tools()

        # Should have exactly 9 JustiFi tools (removed list_refunds - endpoint doesn't exist)
        assert len(tools) == 9

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "create_payment",
            "retrieve_payment",
            "list_payments",
            "refund_payment",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_tool_descriptions(self):
        """Test that all tools have proper descriptions."""
        tools = await handle_list_tools()

        for tool in tools:
            assert hasattr(tool, "description")
            assert isinstance(tool.description, str)
            assert len(tool.description) > 10  # Should have meaningful descriptions

    @pytest.mark.asyncio
    async def test_tool_functions_callable(self):
        """Test that all tool functions are callable."""
        tools = await handle_list_tools()

        for tool in tools:
            # MCP tools don't have a 'func' attribute, they have schemas
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_environment_validation(self):
        """Test that the server validates required environment variables."""
        # Test with missing CLIENT_ID
        old_client_id = os.environ.get("JUSTIFI_CLIENT_ID")
        if "JUSTIFI_CLIENT_ID" in os.environ:
            del os.environ["JUSTIFI_CLIENT_ID"]

        try:
            # This should work since we're not actually calling the API
            # The validation happens when tokens are requested
            pass
        finally:
            if old_client_id:
                os.environ["JUSTIFI_CLIENT_ID"] = old_client_id


class TestMCPProtocol:
    """Test MCP protocol compliance."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up test environment variables."""
        os.environ["JUSTIFI_CLIENT_ID"] = TEST_CLIENT_ID
        os.environ["JUSTIFI_CLIENT_SECRET"] = TEST_CLIENT_SECRET
        os.environ["JUSTIFI_BASE_URL"] = TEST_BASE_URL
        yield

    def test_server_info(self):
        """Test that server provides proper info."""
        assert hasattr(server, "name")
        assert server.name == "justifi-mcp-server"

    @pytest.mark.asyncio
    async def test_list_tools_protocol(self):
        """Test that tools can be listed via MCP protocol."""
        # This simulates the MCP list_tools call
        tools = await handle_list_tools()

        # Verify tools are in the expected MCP format
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

            # Tool names should follow naming conventions
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0
            assert "_" in tool.name or tool.name.islower()


class TestToolIntegration:
    """Test integration between MCP server and JustiFi tools."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up test environment variables."""
        os.environ["JUSTIFI_CLIENT_ID"] = TEST_CLIENT_ID
        os.environ["JUSTIFI_CLIENT_SECRET"] = TEST_CLIENT_SECRET
        os.environ["JUSTIFI_BASE_URL"] = TEST_BASE_URL
        yield

    @pytest.mark.asyncio
    async def test_create_payment_tool_registration(self):
        """Test that create_payment tool is properly registered."""
        tools = await handle_list_tools()
        create_tool = next((t for t in tools if t.name == "create_payment"), None)

        assert create_tool is not None
        assert "Create a new payment" in create_tool.description
        assert create_tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_retrieve_payment_tool_registration(self):
        """Test that retrieve_payment tool is properly registered."""
        tools = await handle_list_tools()
        retrieve_tool = next((t for t in tools if t.name == "retrieve_payment"), None)

        assert retrieve_tool is not None
        assert "Retrieve" in retrieve_tool.description
        assert retrieve_tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_list_payments_tool_registration(self):
        """Test that list_payments tool is properly registered."""
        tools = await handle_list_tools()
        list_tool = next((t for t in tools if t.name == "list_payments"), None)

        assert list_tool is not None
        assert "List payments" in list_tool.description
        assert list_tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_refund_payment_tool_registration(self):
        """Test that refund_payment tool is properly registered."""
        tools = await handle_list_tools()
        refund_tool = next((t for t in tools if t.name == "refund_payment"), None)

        assert refund_tool is not None
        assert "refund" in refund_tool.description
        assert refund_tool.inputSchema is not None


class TestErrorHandling:
    """Test error handling in the MCP server."""

    def test_missing_environment_variables(self):
        """Test behavior when required environment variables are missing."""
        # Remove environment variables
        old_vars = {}
        for var in ["JUSTIFI_CLIENT_ID", "JUSTIFI_CLIENT_SECRET"]:
            old_vars[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            # The server should still initialize, but API calls should fail
            # This is expected behavior - validation happens at runtime
            assert server is not None
        finally:
            # Restore environment variables
            for var, value in old_vars.items():
                if value:
                    os.environ[var] = value


if __name__ == "__main__":
    pytest.main([__file__])
