"""Test LangChain adapter specifically."""

import pytest
import respx
from httpx import Response

from justifi_mcp.adapters.langchain import LangChainAdapter
from justifi_mcp.config import JustiFiConfig
from justifi_mcp.tools.base import ToolError, ValidationError

# Mark all tests as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def basic_config():
    """Create a basic test configuration."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools="all",
    )


@pytest.fixture
def restricted_config():
    """Create a restricted test configuration."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools=["retrieve_payout", "list_payouts"],
    )


@pytest.fixture
def mock_token_response():
    """Mock OAuth token response."""
    return {"access_token": "test_token", "expires_in": 3600}


@pytest.fixture
def mock_payout_data():
    """Mock payout data."""
    return {
        "data": {
            "id": "po_test123",
            "status": "completed",
            "amount": 10000,
            "currency": "USD",
            "created_at": "2025-01-25T12:00:00Z",
        }
    }


class TestLangChainAdapterInitialization:
    """Test LangChain adapter initialization."""

    def test_adapter_initialization(self, basic_config):
        """Test adapter initializes correctly."""
        adapter = LangChainAdapter(basic_config)

        assert adapter.config == basic_config
        assert adapter.client is not None
        assert adapter.client.client_id == "test_client_id"

    # def test_adapter_initialization_missing_credentials(self):
    #     """Test adapter fails with missing credentials."""
    #     from pydantic import ValidationError as PydanticValidationError
    #
    #     with pytest.raises(PydanticValidationError, match="client_id must be provided"):
    #         config = JustiFiConfig(client_id=None, client_secret=None, enabled_tools=[])
    #         LangChainAdapter(config)


class TestLangChainToolCreation:
    """Test LangChain tool creation."""

    def test_get_langchain_tools_all_enabled(self, basic_config):
        """Test getting all enabled LangChain tools."""
        pytest.importorskip("langchain_core")

        adapter = LangChainAdapter(basic_config)
        tools = adapter.get_langchain_tools()

        # Should have 4 tools
        assert len(tools) == 4

        tool_names = [tool.name for tool in tools]
        assert "retrieve_payout" in tool_names
        assert "list_payouts" in tool_names
        assert "get_payout_status" in tool_names
        assert "get_recent_payouts" in tool_names

    def test_get_langchain_tools_restricted(self, restricted_config):
        """Test getting restricted LangChain tools."""
        pytest.importorskip("langchain_core")

        adapter = LangChainAdapter(restricted_config)
        tools = adapter.get_langchain_tools()

        # Should have 2 tools
        assert len(tools) == 2

        tool_names = [tool.name for tool in tools]
        assert "retrieve_payout" in tool_names
        assert "list_payouts" in tool_names
        assert "get_payout_status" not in tool_names
        assert "get_recent_payouts" not in tool_names

    def test_langchain_import_error(self, basic_config):
        """Test graceful handling when LangChain is not available."""
        adapter = LangChainAdapter(basic_config)

        # Mock import error
        def mock_import(name, *args, **kwargs):
            if name == "langchain_core.tools":
                raise ImportError("No module named 'langchain_core'")
            return __import__(name, *args, **kwargs)

        with (
            pytest.MonkeyPatch().context() as m,
            pytest.raises(ImportError, match="LangChain is required"),
        ):
            m.setattr("builtins.__import__", mock_import)
            adapter.get_langchain_tools()

    def test_tool_schemas_format(self, basic_config):
        """Test tool schemas are properly formatted."""
        pytest.importorskip("langchain_core")

        adapter = LangChainAdapter(basic_config)
        tools = adapter.get_langchain_tools()

        # Check retrieve_payout tool
        retrieve_tool = next(tool for tool in tools if tool.name == "retrieve_payout")

        assert retrieve_tool.name == "retrieve_payout"
        assert "retrieve" in retrieve_tool.description.lower()
        assert retrieve_tool.args_schema is not None

        # Check schema properties
        schema = retrieve_tool.args_schema.model_json_schema()
        assert "payout_id" in schema["properties"]
        assert schema["properties"]["payout_id"]["type"] == "string"
        assert "required" in schema
        assert "payout_id" in schema["required"]


class TestLangChainToolExecution:
    """Test LangChain tool execution."""

    @respx.mock
    async def test_tool_execution_success(
        self, basic_config, mock_token_response, mock_payout_data
    ):
        """Test successful tool execution."""
        pytest.importorskip("langchain_core")

        adapter = LangChainAdapter(basic_config)

        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        # Execute tool directly
        result = await adapter.execute_tool("retrieve_payout", payout_id="po_test123")

        assert result == mock_payout_data
        assert result["data"]["id"] == "po_test123"

    async def test_tool_execution_validation_error(self, basic_config):
        """Test tool execution with validation error."""
        adapter = LangChainAdapter(basic_config)

        # Test with empty payout_id
        with pytest.raises(ValidationError, match="payout_id cannot be empty"):
            await adapter.execute_tool("retrieve_payout", payout_id="")

    async def test_tool_execution_disabled_tool(self, restricted_config):
        """Test execution of disabled tool."""
        adapter = LangChainAdapter(restricted_config)

        with pytest.raises(
            ValidationError, match="Tool 'get_payout_status' is not enabled"
        ):
            await adapter.execute_tool("get_payout_status", payout_id="po_test123")

    async def test_tool_execution_unknown_tool(self, basic_config):
        """Test execution of unknown tool."""
        adapter = LangChainAdapter(basic_config)

        with pytest.raises(ValidationError, match="Unknown tool 'nonexistent_tool'"):
            await adapter.execute_tool("nonexistent_tool", arg="value")

    @respx.mock
    async def test_langchain_tool_async_execution(
        self, basic_config, mock_token_response, mock_payout_data
    ):
        """Test that LangChain tools can be executed asynchronously."""
        pytest.importorskip("langchain_core")

        adapter = LangChainAdapter(basic_config)
        tools = adapter.get_langchain_tools()

        # Find retrieve_payout tool
        retrieve_tool = next(tool for tool in tools if tool.name == "retrieve_payout")

        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        # Execute the tool via LangChain interface
        result = retrieve_tool.run({"payout_id": "po_test123"})

        # The result should be a JSON string representation
        import json

        parsed_result = json.loads(result)
        assert parsed_result == mock_payout_data

    @respx.mock
    async def test_tool_execution_with_http_error(self, basic_config):
        """Test tool execution with HTTP error handling."""
        adapter = LangChainAdapter(basic_config)

        # Mock HTTP error response
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(
                200, json={"access_token": "test_token", "expires_in": 3600}
            )
        )
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(404, json={"error": "Payout not found"})
        )

        with pytest.raises(ToolError, match="Resource not found"):
            await adapter.execute_tool("retrieve_payout", payout_id="po_test123")

    @respx.mock
    async def test_tool_execution_with_network_error(self, basic_config):
        """Test tool execution with network error handling."""
        adapter = LangChainAdapter(basic_config)

        # Mock network error
        from unittest.mock import patch

        import httpx

        with patch.object(
            adapter.client, "request", side_effect=httpx.ConnectError("Network error")
        ):
            with pytest.raises(ToolError, match="Network error"):
                await adapter.execute_tool("retrieve_payout", payout_id="po_test123")


class TestLangChainSchemas:
    """Test LangChain schema functionality."""

    def test_get_tool_schemas(self, basic_config):
        """Test getting tool schemas in LangChain format."""
        adapter = LangChainAdapter(basic_config)
        schemas = adapter.get_tool_schemas()

        assert len(schemas) == 4  # All tools enabled

        # Check schema structure
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            assert "framework" in schema
            assert schema["framework"] == "langchain"

    def test_get_tool_schemas_restricted(self, restricted_config):
        """Test getting tool schemas with restricted tools."""
        adapter = LangChainAdapter(restricted_config)
        schemas = adapter.get_tool_schemas()

        assert len(schemas) == 2  # Only 2 tools enabled

        schema_names = [schema["name"] for schema in schemas]
        assert "retrieve_payout" in schema_names
        assert "list_payouts" in schema_names


class TestLangChainErrorHandling:
    """Test LangChain adapter error handling."""

    @respx.mock
    async def test_http_error_handling(self, basic_config, mock_token_response):
        """Test handling of HTTP errors."""
        adapter = LangChainAdapter(basic_config)

        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock 404 response
        respx.get("https://api.justifi.ai/v1/payouts/po_notfound").mock(
            return_value=Response(404, json={"error": "Payout not found"})
        )

        with pytest.raises(ToolError):
            await adapter.execute_tool("retrieve_payout", payout_id="po_notfound")

    async def test_unexpected_error_wrapping(self, basic_config):
        """Test that unexpected errors are properly wrapped."""
        adapter = LangChainAdapter(basic_config)

        # Mock a tool function that raises an unexpected error
        from unittest.mock import patch

        async def mock_request(*args, **kwargs):
            raise RuntimeError("Unexpected error")

        with patch.object(adapter.client, "request", side_effect=mock_request):
            with pytest.raises(ToolError, match="Unexpected error"):
                await adapter.execute_tool("retrieve_payout", payout_id="po_test123")


class TestLangChainIntegration:
    """Test integration scenarios with LangChain."""

    def test_adapter_compatibility_with_toolkit(self, basic_config):
        """Test that adapter is compatible with main toolkit."""
        from justifi_mcp import JustiFiToolkit

        toolkit = JustiFiToolkit(config=basic_config)

        # Should be able to get LangChain tools via toolkit
        try:
            tools = toolkit.get_langchain_tools()
            assert len(tools) == 4
        except ImportError:
            pytest.skip("LangChain not available")

    def test_adapter_lazy_loading(self, basic_config):
        """Test that adapter supports lazy loading."""
        from justifi_mcp import JustiFiToolkit

        toolkit = JustiFiToolkit(config=basic_config)

        # Adapter should be None initially (not a real adapter instance)
        assert toolkit._langchain_adapter is None

        # Should be loaded after first use
        try:
            toolkit.get_langchain_tools()
            assert hasattr(toolkit, "_langchain_adapter")
            assert toolkit._langchain_adapter is not None
        except ImportError:
            pytest.skip("LangChain not available")
