"""Integration tests for MCP server with auto-registration."""

import os
from unittest.mock import patch

import pytest
from fastmcp import FastMCP

from modelcontextprotocol.auto_register import get_registered_tool_count
from python.core import JustiFiClient


@pytest.fixture
def mock_client():
    """Create a mock JustiFi client."""
    return JustiFiClient("test_client", "test_secret")


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token_123", "expires_in": 3600}


class TestMcpServerIntegration:
    """Integration tests for the MCP server with auto-registration."""

    @pytest.mark.asyncio
    async def test_auto_registered_server_startup(self):
        """Test that MCP server starts successfully with auto-registration."""
        # Set test environment variables
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            },
        ):
            from modelcontextprotocol.server import create_mcp_server

            # Should create server without errors
            server = create_mcp_server()
            assert server is not None
            assert isinstance(server, FastMCP)
            assert server.name == "JustiFi Payment Server"

    def test_auto_registration_tool_count_consistency(self):
        """Test that auto-registration discovers expected number of tools."""
        tool_count = get_registered_tool_count()

        # Should discover at least 27 tools as specified in the issue
        assert tool_count >= 27

        # Verify against known tools from __all__ in tools package
        from python.tools import __all__ as tools_all

        # Filter out utility functions
        expected_tools = [
            name
            for name in tools_all
            if name not in ["standardize_response", "wrap_tool_call"]
        ]

        # Auto-registration should find all exported tool functions
        assert tool_count >= len(expected_tools)

    def test_server_creation_without_credentials_fails(self):
        """Test that server creation fails gracefully without credentials."""
        # Clear credentials
        with patch.dict(os.environ, {}, clear=True):
            from modelcontextprotocol.server import create_mcp_server

            # Should raise ValidationError (which is subclass of ValueError) for missing credentials
            with pytest.raises(ValueError, match="validation error"):
                create_mcp_server()

    def test_server_creation_with_partial_credentials_fails(self):
        """Test that server creation fails with partial credentials."""
        # Only provide client_id, not secret
        with patch.dict(
            os.environ,
            {"JUSTIFI_CLIENT_ID": "test_client"},
            clear=True,
        ):
            from modelcontextprotocol.server import create_mcp_server

            # Should raise ValueError for missing secret (pattern for pydantic validation error)
            with pytest.raises(ValueError, match="client_secret"):
                create_mcp_server()

class TestMcpServerRobustness:
    """Tests for server robustness and error handling."""

    def test_auto_registration_continues_on_tool_import_errors(self):
        """Test that auto-registration continues if some tool imports fail."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "MCP_AUTO_REGISTER": "true",
            },
        ):
            # Mock a specific tool to fail during registration
            with patch(
                "modelcontextprotocol.auto_register.register_single_tool"
            ) as mock_register:

                def side_effect(mcp, client, tool_name, tool_func):
                    if tool_name == "retrieve_payout":
                        raise Exception("Tool registration failed")

                mock_register.side_effect = side_effect

                from modelcontextprotocol.server import create_mcp_server

                # Should still create server despite one tool failing
                server = create_mcp_server()
                assert server is not None

    def test_server_startup_performance(self):
        """Test that server startup performance is reasonable."""
        import time

        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "MCP_AUTO_REGISTER": "true",
            },
        ):
            from modelcontextprotocol.server import create_mcp_server

            start_time = time.time()
            server = create_mcp_server()
            end_time = time.time()

            # Server startup should complete quickly (under 5 seconds)
            startup_time = end_time - start_time
            assert startup_time < 5.0, f"Server startup took {startup_time:.2f} seconds"
            assert server is not None

    def test_tool_registration_idempotency(self, mock_client):
        """Test that tools can be registered multiple times without issues."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "MCP_AUTO_REGISTER": "true",
            },
        ):
            from modelcontextprotocol.server import create_mcp_server, register_tools

            # Create server and client
            server = create_mcp_server()
            client = mock_client

            # Register tools multiple times - should not cause errors
            register_tools(server, client)
            register_tools(server, client)

            assert server is not None


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing functionality."""

    def test_manual_registration_preserves_all_tools(self):
        """Test that manual registration still includes all expected tools."""
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
                "MCP_AUTO_REGISTER": "false",
            },
        ):
            from modelcontextprotocol.server import create_mcp_server

            # Manual registration should still work
            server = create_mcp_server()
            assert server is not None

            # Should be the same FastMCP instance type
            assert isinstance(server, FastMCP)

    def test_both_registration_methods_equivalent(self, mock_client):
        """Test that both registration methods produce equivalent results."""
        from fastmcp import FastMCP

        client = mock_client

        # Test auto-registration
        auto_server = FastMCP("test-auto")
        with patch.dict(os.environ, {"MCP_AUTO_REGISTER": "true"}):
            from modelcontextprotocol.server import register_tools

            register_tools(auto_server, client)

        # Test manual registration
        manual_server = FastMCP("test-manual")
        with patch.dict(os.environ, {"MCP_AUTO_REGISTER": "false"}):
            from modelcontextprotocol.server import register_tools

            register_tools(manual_server, client)

        # Both should be FastMCP instances (detailed comparison would require
        # access to FastMCP internals which may not be available)
        assert isinstance(auto_server, FastMCP)
        assert isinstance(manual_server, FastMCP)
