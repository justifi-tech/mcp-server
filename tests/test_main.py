"""Test suite for the JustiFi Payout MCP Server.

Tests MCP protocol compliance and payout tool registration.
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
TEST_BASE_URL = "https://api.justifi.ai/v1"


class TestPayoutMCPServer:
    """Test payout-focused MCP server initialization and functionality."""

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
        assert server.name == "justifi-payout-mcp-server"

    @pytest.mark.asyncio
    async def test_payout_tools_registration(self):
        """Test that payout tools are properly registered."""
        tools = await handle_list_tools()

        # Should have exactly 4 payout tools
        assert len(tools) == 4

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "get_recent_payouts",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_tool_descriptions(self):
        """Test that all payout tools have proper descriptions."""
        tools = await handle_list_tools()

        for tool in tools:
            assert hasattr(tool, "description")
            assert isinstance(tool.description, str)
            assert len(tool.description) > 10  # Should have meaningful descriptions
            # All tools should be payout-related
            assert "payout" in tool.description.lower()

    @pytest.mark.asyncio
    async def test_tool_schemas(self):
        """Test that all tools have proper input schemas."""
        tools = await handle_list_tools()

        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

    @pytest.mark.asyncio
    async def test_retrieve_payout_tool(self):
        """Test retrieve_payout tool registration."""
        tools = await handle_list_tools()
        retrieve_tool = next((t for t in tools if t.name == "retrieve_payout"), None)

        assert retrieve_tool is not None
        assert "retrieve details" in retrieve_tool.description.lower()
        assert "payout_id" in retrieve_tool.inputSchema["properties"]
        assert retrieve_tool.inputSchema["required"] == ["payout_id"]

    @pytest.mark.asyncio
    async def test_list_payouts_tool(self):
        """Test list_payouts tool registration."""
        tools = await handle_list_tools()
        list_tool = next((t for t in tools if t.name == "list_payouts"), None)

        assert list_tool is not None
        assert "list payouts" in list_tool.description.lower()
        assert "limit" in list_tool.inputSchema["properties"]
        assert "after_cursor" in list_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_get_payout_status_tool(self):
        """Test get_payout_status tool registration."""
        tools = await handle_list_tools()
        status_tool = next((t for t in tools if t.name == "get_payout_status"), None)

        assert status_tool is not None
        assert "status" in status_tool.description.lower()
        assert "payout_id" in status_tool.inputSchema["properties"]
        assert status_tool.inputSchema["required"] == ["payout_id"]

    @pytest.mark.asyncio
    async def test_get_recent_payouts_tool(self):
        """Test get_recent_payouts tool registration."""
        tools = await handle_list_tools()
        recent_tool = next((t for t in tools if t.name == "get_recent_payouts"), None)

        assert recent_tool is not None
        assert "recent" in recent_tool.description.lower()
        assert "limit" in recent_tool.inputSchema["properties"]


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
        assert server.name == "justifi-payout-mcp-server"

    @pytest.mark.asyncio
    async def test_list_tools_protocol(self):
        """Test that tools can be listed via MCP protocol."""
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
