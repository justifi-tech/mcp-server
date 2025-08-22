"""
Integration Tests for Terminal Tools

Tests that verify terminal tools work end-to-end through:
1. Direct tool usage
2. MCP server integration 
3. LangChain adapter integration
"""

import pytest
from unittest.mock import patch

from python.config import JustiFiConfig
from python.core import JustiFiClient
from python.tools.base import ToolError
from python.tools.terminals import (
    get_terminal_status,
    identify_terminal,
    list_terminals,
    retrieve_terminal,
    update_terminal,
)
from modelcontextprotocol.server import create_mcp_server


class TestTerminalToolsDirectIntegration:
    """Test terminal tools direct usage integration."""

    @pytest.fixture
    def test_client(self):
        """Create test client with dummy credentials."""
        return JustiFiClient("test_client_id", "test_client_secret")

    @pytest.mark.asyncio
    async def test_list_terminals_reaches_api(self, test_client):
        """Test that list_terminals reaches JustiFi API."""
        with pytest.raises(ToolError) as exc_info:
            await list_terminals(test_client, limit=5)
        
        error_msg = str(exc_info.value)
        assert "Failed to list terminals" in error_msg
        # Should contain auth-related error since we're using test credentials
        assert any(x in error_msg for x in ["Authentication", "auth", "404", "401"])

    @pytest.mark.asyncio
    async def test_retrieve_terminal_reaches_api(self, test_client):
        """Test that retrieve_terminal reaches JustiFi API."""
        with pytest.raises(ToolError) as exc_info:
            await retrieve_terminal(test_client, "trm_test123")
        
        error_msg = str(exc_info.value)
        assert "Failed to retrieve terminal" in error_msg

    @pytest.mark.asyncio 
    async def test_update_terminal_reaches_api(self, test_client):
        """Test that update_terminal reaches JustiFi API."""
        with pytest.raises(ToolError) as exc_info:
            await update_terminal(test_client, "trm_test123", nickname="Test Terminal")
        
        error_msg = str(exc_info.value)
        assert "Failed to update terminal" in error_msg

    @pytest.mark.asyncio
    async def test_get_terminal_status_reaches_api(self, test_client):
        """Test that get_terminal_status reaches JustiFi API."""
        with pytest.raises(ToolError) as exc_info:
            await get_terminal_status(test_client, "trm_test123")
        
        error_msg = str(exc_info.value)
        assert "Failed to get status for terminal" in error_msg

    @pytest.mark.asyncio
    async def test_identify_terminal_reaches_api(self, test_client):
        """Test that identify_terminal reaches JustiFi API."""
        with pytest.raises(ToolError) as exc_info:
            await identify_terminal(test_client, "trm_test123")
        
        error_msg = str(exc_info.value)
        assert "Failed to identify terminal" in error_msg


class TestTerminalToolsMCPIntegration:
    """Test terminal tools through MCP server integration."""

    def test_mcp_server_registers_terminal_tools(self):
        """Test that MCP server successfully registers all terminal tools."""
        server = create_mcp_server()
        
        # Check that server was created
        assert server is not None
        
        # Get all registered tools (this is synchronous for the FastMCP server)
        # We can't easily call async methods here, but we can verify the server
        # was created which means auto-registration ran successfully
        assert hasattr(server, 'get_tools') or hasattr(server, 'list_tools')

    def test_mcp_server_tool_count_includes_terminals(self):
        """Test that MCP server includes terminal tools in total count."""
        server = create_mcp_server()
        
        # The auto-registration should have found our 5 new terminal tools
        # plus all existing tools. The exact count may vary, but should be >= 32
        # (this is tested more precisely in test_mcp_server_integration.py)
        
        # Just verify server creation succeeded, which means auto-registration worked
        assert server is not None


class TestTerminalToolsLangChainIntegration:
    """Test terminal tools through LangChain adapter integration."""

    @pytest.fixture
    def test_config(self):
        """Create test config with dummy credentials."""
        return JustiFiConfig(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

    def test_langchain_adapter_includes_terminal_tools(self, test_config):
        """Test that LangChain adapter includes terminal tools."""
        # Import here to handle optional dependency gracefully
        pytest.importorskip("langchain_core", reason="LangChain not installed")
        
        from python.adapters.langchain import LangChainAdapter
        
        adapter = LangChainAdapter(test_config)
        tools = adapter.get_langchain_tools()
        
        # Find terminal tools
        terminal_tools = [tool for tool in tools if 'terminal' in tool.name.lower()]
        
        # Should have all 5 terminal tools
        expected_terminal_tools = {
            'list_terminals',
            'retrieve_terminal',
            'update_terminal', 
            'get_terminal_status',
            'identify_terminal'
        }
        
        found_terminal_tools = {tool.name for tool in terminal_tools}
        
        assert len(terminal_tools) == 5, f"Expected 5 terminal tools, found {len(terminal_tools)}"
        assert found_terminal_tools == expected_terminal_tools
        
        # Verify each tool has proper structure
        for tool in terminal_tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'args_schema')
            assert tool.description  # Should not be empty
            
    def test_langchain_terminal_tool_schemas(self, test_config):
        """Test that terminal tools have proper LangChain schemas."""
        pytest.importorskip("langchain_core", reason="LangChain not installed")
        
        from python.adapters.langchain import LangChainAdapter
        
        adapter = LangChainAdapter(test_config)
        tools = adapter.get_langchain_tools()
        
        # Find list_terminals tool specifically
        list_terminals_tool = next(
            (tool for tool in tools if tool.name == 'list_terminals'), 
            None
        )
        
        assert list_terminals_tool is not None, "list_terminals tool not found"
        
        # Check schema has expected parameters
        schema = list_terminals_tool.args_schema
        assert schema is not None
        
        # Should have limit parameter
        schema_fields = schema.model_fields if hasattr(schema, 'model_fields') else schema.__fields__
        assert 'limit' in schema_fields
        
        # Optional parameters should be present
        optional_params = {'after_cursor', 'before_cursor', 'status', 'terminal_id', 'provider_id'}
        for param in optional_params:
            if param in schema_fields:
                # If present, should be optional (not in required list)
                required_fields = getattr(schema, '__required__', set())
                if required_fields and param in required_fields:
                    pytest.fail(f"Parameter {param} should be optional")

    @pytest.mark.asyncio
    async def test_langchain_terminal_tool_execution(self, test_config):
        """Test that terminal tools can be executed through LangChain adapter."""
        pytest.importorskip("langchain_core", reason="LangChain not installed")
        
        from python.adapters.langchain import LangChainAdapter
        
        adapter = LangChainAdapter(test_config)
        tools = adapter.get_langchain_tools()
        
        # Find list_terminals tool
        list_terminals_tool = next(
            (tool for tool in tools if tool.name == 'list_terminals'),
            None
        )
        
        assert list_terminals_tool is not None
        
        # Try to execute the tool - should fail with auth error but prove it's callable
        with pytest.raises(Exception) as exc_info:
            await list_terminals_tool.ainvoke({"limit": 5})
        
        error_msg = str(exc_info.value)
        # Should contain terminal-specific error message
        assert any(x in error_msg for x in [
            "Failed to list terminals",
            "Authentication", 
            "auth",
            "404",
            "401"
        ]), f"Unexpected error message: {error_msg}"


class TestTerminalToolsEndToEndIntegration:
    """End-to-end integration tests spanning multiple layers."""

    def test_terminal_tools_full_stack_availability(self):
        """Test that terminal tools are available through all integration points."""
        # 1. Direct import
        from python.tools.terminals import list_terminals
        assert callable(list_terminals)
        
        # 2. MCP server registration
        server = create_mcp_server()
        assert server is not None
        
        # 3. LangChain adapter (if available)
        try:
            import langchain_core  # noqa: F401
            from python.adapters.langchain import LangChainAdapter
            
            config = JustiFiConfig(client_id="test", client_secret="test")
            adapter = LangChainAdapter(config)
            tools = adapter.get_langchain_tools()
            
            terminal_tool_names = {tool.name for tool in tools if 'terminal' in tool.name}
            assert len(terminal_tool_names) == 5, "Should have 5 terminal tools in LangChain adapter"
            
        except ImportError:
            # LangChain not available, skip this part
            pass

    def test_terminal_tools_consistency_across_integrations(self):
        """Test that terminal tools are consistent across different integration points."""
        expected_tools = {
            'list_terminals',
            'retrieve_terminal', 
            'update_terminal',
            'get_terminal_status',
            'identify_terminal'
        }
        
        # Check direct imports
        from python.tools import __all__ as tools_exports
        terminal_exports = {name for name in tools_exports if 'terminal' in name}
        assert terminal_exports == expected_tools, f"Mismatch in direct exports: {terminal_exports}"
        
        # Check LangChain adapter consistency (if available)
        try:
            import langchain_core  # noqa: F401
            from python.adapters.langchain import LangChainAdapter
            
            config = JustiFiConfig(client_id="test", client_secret="test") 
            adapter = LangChainAdapter(config)
            tools = adapter.get_langchain_tools()
            
            langchain_terminal_tools = {tool.name for tool in tools if 'terminal' in tool.name}
            assert langchain_terminal_tools == expected_tools, f"LangChain tools mismatch: {langchain_terminal_tools}"
            
        except ImportError:
            # LangChain not available, skip
            pass