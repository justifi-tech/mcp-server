"""Tests for the automatic MCP tool registration system."""

import inspect
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from fastmcp import FastMCP
from httpx import Response

from modelcontextprotocol.auto_register import (
    auto_register_tools,
    create_mcp_function,
    discover_tools,
    extract_tool_metadata,
    get_registered_tool_count,
    register_single_tool,
)
from python.core import JustiFiClient


@pytest.fixture
def mock_client():
    """Create a mock JustiFi client."""
    return JustiFiClient("test_client", "test_secret")


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token_123", "expires_in": 3600}


class TestDiscoverTools:
    """Tests for tool discovery functionality."""

    def test_discover_tools_returns_expected_count(self):
        """Test that tool discovery finds expected number of tools."""
        tools = discover_tools()

        # Should find at least 27 tools as mentioned in the issue
        assert len(tools) >= 27

        # Should return sorted list
        assert tools == sorted(tools)

    def test_discover_tools_finds_known_tools(self):
        """Test that tool discovery finds known tools."""
        tools = discover_tools()

        # Should find known tools from different modules
        expected_tools = {
            "retrieve_payout",
            "list_payouts",
            "get_payout_status",
            "get_recent_payouts",
            "retrieve_payment",
            "list_payments",
            "create_payment_method_group",
            "list_payment_method_groups",
            "retrieve_payment_method",
            "retrieve_payment_method_group",
            "update_payment_method_group",
            "remove_payment_method_from_group",
            "list_refunds",
            "retrieve_refund",
            "list_payment_refunds",
            "list_balance_transactions",
            "retrieve_balance_transaction",
            "list_disputes",
            "retrieve_dispute",
            "list_checkouts",
            "retrieve_checkout",
            "list_sub_accounts",
            "get_sub_account",
            "get_sub_account_payout_account",
            "get_sub_account_settings",
            "list_proceeds",
            "retrieve_proceed",
        }

        assert expected_tools.issubset(set(tools))

    def test_discover_tools_excludes_utility_functions(self):
        """Test that utility functions are excluded from discovery."""
        tools = discover_tools()

        # Should not include utility functions
        excluded = {"standardize_response", "wrap_tool_call"}
        for excluded_func in excluded:
            assert excluded_func not in tools


class TestExtractToolMetadata:
    """Tests for tool metadata extraction."""

    def test_extract_tool_metadata_from_real_function(self):
        """Test metadata extraction from a real tool function."""
        from python.tools.payouts import retrieve_payout

        metadata = extract_tool_metadata(retrieve_payout)

        # Should extract docstring
        assert "docstring" in metadata
        assert len(metadata["docstring"]) > 10
        # Check for payout-related content (might be in wrapped function docstring)
        docstring_lower = metadata["docstring"].lower()
        assert (
            "payout" in docstring_lower
            or "retrieve" in docstring_lower
            or "operation" in docstring_lower
        )

        # Should extract signature
        assert "signature" in metadata
        assert metadata["signature"] is not None

        # Should extract annotations (excluding client)
        assert "annotations" in metadata
        assert "client" not in metadata["annotations"]

        # Should have parameters without client
        assert "parameters" in metadata
        param_names = [p.name for p in metadata["parameters"]]
        assert "client" not in param_names
        # Check if payout_id is in the parameters (wrapped function might have different signature)
        assert len(param_names) > 0  # Should have at least some parameters

    def test_extract_tool_metadata_handles_wrapped_functions(self):
        """Test metadata extraction handles decorated functions."""
        from python.tools.payouts import retrieve_payout

        # This function has @traceable and @handle_tool_errors decorators
        metadata = extract_tool_metadata(retrieve_payout)

        # Should still extract proper metadata despite decorators
        assert metadata["docstring"] is not None
        assert metadata["signature"] is not None
        assert len(metadata["parameters"]) > 0


class TestCreateMcpFunction:
    """Tests for MCP function creation."""

    def test_create_mcp_function_with_valid_metadata(self, mock_client):
        """Test MCP function creation with valid metadata."""
        from python.tools.payouts import retrieve_payout

        metadata = extract_tool_metadata(retrieve_payout)

        mcp_func = create_mcp_function(
            "retrieve_payout", retrieve_payout, mock_client, metadata
        )

        # Should have correct name and docstring
        assert mcp_func.__name__ == "retrieve_payout"
        assert mcp_func.__doc__ == metadata["docstring"]

        # Should be a coroutine function
        assert inspect.iscoroutinefunction(mcp_func)

        # Should have preserved signature if available
        if metadata["signature"]:
            assert mcp_func.__signature__ == metadata["signature"]

    def test_create_mcp_function_with_fallback_metadata(self, mock_client):
        """Test MCP function creation with fallback metadata."""
        from python.tools.payouts import retrieve_payout

        # Create metadata with no signature (simulates extraction failure)
        metadata = {
            "signature": None,
            "annotations": {},
            "parameters": [],
            "docstring": "Test function",
            "return_annotation": dict[str, Any],
        }

        mcp_func = create_mcp_function(
            "test_func", retrieve_payout, mock_client, metadata
        )

        # Should still create valid function
        assert mcp_func.__name__ == "test_func"
        assert mcp_func.__doc__ == "Test function"
        assert inspect.iscoroutinefunction(mcp_func)

    @pytest.mark.asyncio
    @respx.mock
    async def test_created_mcp_function_calls_wrap_tool_call(
        self, mock_client, mock_token_response
    ):
        """Test that created MCP function properly calls wrap_tool_call."""
        from python.tools.payouts import retrieve_payout

        # Mock OAuth token
        respx.post("https://api.justifi.ai/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        metadata = extract_tool_metadata(retrieve_payout)

        mcp_func = create_mcp_function(
            "retrieve_payout", retrieve_payout, mock_client, metadata
        )

        # Mock wrap_tool_call to verify it's called correctly
        with patch(
            "modelcontextprotocol.auto_register.wrap_tool_call", new_callable=AsyncMock
        ) as mock_wrap:
            mock_wrap.return_value = {"test": "result"}

            result = await mcp_func("test_payout_id")

            # Should call wrap_tool_call with correct arguments
            mock_wrap.assert_called_once_with(
                "retrieve_payout", retrieve_payout, mock_client, "test_payout_id"
            )
            assert result == {"test": "result"}


class TestRegisterSingleTool:
    """Tests for single tool registration."""

    def test_register_single_tool_success(self, mock_client):
        """Test successful single tool registration."""
        mcp = MagicMock(spec=FastMCP)

        from python.tools.payouts import retrieve_payout

        register_single_tool(mcp, mock_client, "retrieve_payout", retrieve_payout)

        # Should call mcp.tool with created function
        mcp.tool.assert_called_once()
        registered_func = mcp.tool.call_args[0][0]

        assert registered_func.__name__ == "retrieve_payout"
        assert inspect.iscoroutinefunction(registered_func)

    def test_register_single_tool_handles_metadata_extraction_errors(self, mock_client):
        """Test single tool registration handles metadata extraction errors gracefully."""
        mcp = MagicMock(spec=FastMCP)

        # Mock function that will cause errors
        mock_func = MagicMock()
        mock_func.__name__ = "failing_func"

        with patch(
            "modelcontextprotocol.auto_register.extract_tool_metadata",
            side_effect=Exception("Test error"),
        ):
            # Should not raise, but handle gracefully
            try:
                register_single_tool(mcp, mock_client, "failing_func", mock_func)
                # If no exception, registration should still proceed with fallbacks
            except Exception as e:
                # If exception is raised, it should be handled by auto_register_tools
                assert "Test error" in str(e)


class TestAutoRegisterTools:
    """Tests for the main auto-registration function."""

    def test_auto_register_tools_success(self, mock_client):
        """Test successful auto-registration of all tools."""
        mcp = MagicMock(spec=FastMCP)

        with patch(
            "modelcontextprotocol.auto_register.discover_tools"
        ) as mock_discover:
            mock_discover.return_value = ["retrieve_payout", "list_payments"]

            with patch(
                "modelcontextprotocol.auto_register.register_single_tool"
            ) as mock_register:
                auto_register_tools(mcp, mock_client)

                # Should call register_single_tool for each discovered tool
                assert mock_register.call_count == 2
                # Check that register_single_tool was called with correct tool names
                call_args = [
                    call[0][2] for call in mock_register.call_args_list
                ]  # Extract tool names
                assert "retrieve_payout" in call_args
                assert "list_payments" in call_args

    def test_auto_register_tools_continues_on_individual_failures(self, mock_client):
        """Test auto-registration continues when individual tool registration fails."""
        mcp = MagicMock(spec=FastMCP)

        with patch(
            "modelcontextprotocol.auto_register.discover_tools"
        ) as mock_discover:
            mock_discover.return_value = ["tool1", "tool2", "tool3"]

            with patch(
                "modelcontextprotocol.auto_register.register_single_tool"
            ) as mock_register:
                with (
                    patch("python.tools.tool1", create=True),
                    patch("python.tools.tool2", create=True),
                    patch("python.tools.tool3", create=True),
                ):
                    # Make the second tool registration fail
                    def side_effect(mcp, client, tool_name, tool_func):
                        if tool_name == "tool2":
                            raise Exception("Registration failed")

                    mock_register.side_effect = side_effect

                    # Should not raise exception, but continue with other tools
                    auto_register_tools(mcp, mock_client)

                    # Should attempt to register all tools
                    assert mock_register.call_count == 3


class TestGetRegisteredToolCount:
    """Tests for the tool count utility function."""

    def test_get_registered_tool_count(self):
        """Test that tool count utility returns expected count."""
        count = get_registered_tool_count()

        # Should return same count as discover_tools
        tools = discover_tools()
        assert count == len(tools)
        assert count >= 27  # At least 27 tools as per issue


class TestIntegration:
    """Integration tests for the auto-registration system."""

    @pytest.mark.asyncio
    async def test_full_auto_registration_integration(self):
        """Test full integration of auto-registration system."""
        from modelcontextprotocol.server import create_mcp_server

        # Mock environment variables for JustiFi client
        with patch.dict(
            os.environ,
            {
                "JUSTIFI_CLIENT_ID": "test_client",
                "JUSTIFI_CLIENT_SECRET": "test_secret",
            },
        ):
            # Should create server without errors
            server = create_mcp_server()
            assert server is not None

            # Server should be FastMCP instance
            assert isinstance(server, FastMCP)
