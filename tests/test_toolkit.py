"""Test JustiFi toolkit functionality."""

import json
from unittest.mock import patch

import pytest
import respx
from httpx import Response

from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit

# Mark all tests as async
pytestmark = pytest.mark.asyncio


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


@pytest.fixture
def basic_config():
    """Basic test configuration with all tools enabled."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools="all",
    )


@pytest.fixture
def restricted_config():
    """Restricted configuration with only some tools enabled."""
    return JustiFiConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        enabled_tools=["retrieve_payout", "list_payouts"],  # Only these enabled
    )


class TestJustiFiToolkitInitialization:
    """Test toolkit initialization."""

    @patch.dict(
        "os.environ",
        {
            "JUSTIFI_CLIENT_ID": "env_client_id",
            "JUSTIFI_CLIENT_SECRET": "env_client_secret",
        },
    )
    def test_toolkit_from_environment(self):
        """Test toolkit initialization from environment variables."""
        toolkit = JustiFiToolkit()
        assert toolkit.config.client_id == "env_client_id"
        assert toolkit.config.client_secret == "env_client_secret"

    def test_toolkit_from_parameters(self):
        """Test toolkit initialization from parameters."""
        toolkit = JustiFiToolkit(
            client_id="param_client_id", client_secret="param_client_secret"
        )
        assert toolkit.config.client_id == "param_client_id"
        assert toolkit.config.client_secret == "param_client_secret"

    def test_toolkit_from_configuration_dict(self):
        """Test toolkit initialization from configuration dictionary."""
        config_dict = {
            "client_id": "dict_client_id",
            "client_secret": "dict_client_secret",
            "enabled_tools": [
                "retrieve_payout",
                "list_payouts",
                "get_payout_status",
            ],  # Exclude get_recent_payouts
            "context": {"environment": "production", "timeout": 15},
        }

        toolkit = JustiFiToolkit(configuration=config_dict)
        assert toolkit.config.client_id == "dict_client_id"
        assert toolkit.config.context.environment == "production"
        assert toolkit.config.is_tool_enabled("get_recent_payouts") is False

    def test_toolkit_from_config_object(self, basic_config):
        """Test toolkit initialization from JustiFiConfig object."""
        toolkit = JustiFiToolkit(config=basic_config)
        assert toolkit.config == basic_config

    @patch.dict("os.environ", {}, clear=True)
    def test_toolkit_missing_credentials(self):
        """Test toolkit initialization with missing credentials."""
        with pytest.raises(ValueError):
            JustiFiToolkit()


class TestToolkitToolManagement:
    """Test toolkit tool management functionality."""

    def test_get_enabled_tools_all_enabled(self, basic_config):
        """Test getting enabled tools when all are enabled."""
        toolkit = JustiFiToolkit(config=basic_config)
        enabled_tools = toolkit.get_enabled_tools()

        assert len(enabled_tools) == 4
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools
        assert "get_payout_status" in enabled_tools
        assert "get_recent_payouts" in enabled_tools

    def test_get_enabled_tools_restricted(self, restricted_config):
        """Test getting enabled tools with restrictions."""
        toolkit = JustiFiToolkit(config=restricted_config)
        enabled_tools = toolkit.get_enabled_tools()

        assert len(enabled_tools) == 2
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools
        assert "get_payout_status" not in enabled_tools
        assert "get_recent_payouts" not in enabled_tools

    def test_get_tool_schemas_all_enabled(self, basic_config):
        """Test getting tool schemas when all tools are enabled."""
        toolkit = JustiFiToolkit(config=basic_config)
        schemas = toolkit.get_tool_schemas()

        assert len(schemas) == 4
        schema_names = [schema.name for schema in schemas]
        assert "retrieve_payout" in schema_names
        assert "list_payouts" in schema_names
        assert "get_payout_status" in schema_names
        assert "get_recent_payouts" in schema_names

    def test_get_tool_schemas_restricted(self, restricted_config):
        """Test getting tool schemas with restrictions."""
        toolkit = JustiFiToolkit(config=restricted_config)
        schemas = toolkit.get_tool_schemas()

        assert len(schemas) == 2
        schema_names = [schema.name for schema in schemas]
        assert "retrieve_payout" in schema_names
        assert "list_payouts" in schema_names
        assert "get_payout_status" not in schema_names
        assert "get_recent_payouts" not in schema_names


class TestToolkitToolExecution:
    """Test toolkit tool execution."""

    @respx.mock
    async def test_call_tool_success(
        self, basic_config, mock_token_response, mock_payout_data
    ):
        """Test successful tool execution."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payout retrieval
        respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
            return_value=Response(200, json=mock_payout_data)
        )

        toolkit = JustiFiToolkit(config=basic_config)
        result = await toolkit.call_tool("retrieve_payout", {"payout_id": "po_test123"})

        assert len(result) == 1
        # Check that response includes success indicator and contains the data
        response_text = result[0].text
        assert "✅ Success:" in response_text
        assert "po_test123" in response_text
        assert "completed" in response_text

        # Extract JSON from the formatted response
        json_start = response_text.find("{")
        json_part = response_text[json_start:]
        response_data = json.loads(json_part)
        assert response_data["data"]["id"] == "po_test123"

    async def test_call_tool_disabled(self, restricted_config):
        """Test calling a disabled tool."""
        toolkit = JustiFiToolkit(config=restricted_config)
        result = await toolkit.call_tool(
            "get_payout_status", {"payout_id": "po_test123"}
        )

        assert len(result) == 1
        assert "not enabled" in result[0].text
        assert "Available tools:" in result[0].text

    async def test_call_tool_unknown(self, basic_config):
        """Test calling an unknown tool."""
        toolkit = JustiFiToolkit(config=basic_config)
        result = await toolkit.call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "not enabled" in result[0].text

    async def test_call_tool_error(self, basic_config):
        """Test tool execution error handling."""
        toolkit = JustiFiToolkit(config=basic_config)
        # Call with invalid arguments to trigger error
        result = await toolkit.call_tool("retrieve_payout", {"payout_id": ""})

        assert len(result) == 1
        assert (
            "Input Error" in result[0].text
            or "payout_id cannot be empty" in result[0].text
        )
        assert "ValidationError" in result[0].text


class TestToolkitMCPIntegration:
    """Test toolkit MCP server integration."""

    def test_get_mcp_server(self, basic_config):
        """Test getting MCP server instance."""
        toolkit = JustiFiToolkit(config=basic_config)
        server = toolkit.get_mcp_server()

        assert server is not None
        assert server.name == "justifi-toolkit-mcp-server"

    def test_get_mcp_server_custom_name(self, basic_config):
        """Test getting MCP server with custom name."""
        toolkit = JustiFiToolkit(config=basic_config)
        server = toolkit.get_mcp_server("custom-server-name")

        assert server.name == "custom-server-name"


class TestToolkitConfiguration:
    """Test toolkit configuration management."""

    def test_get_configuration_summary(self, basic_config):
        """Test getting configuration summary."""
        toolkit = JustiFiToolkit(config=basic_config)
        summary = toolkit.get_configuration_summary()

        assert "environment" in summary
        assert "base_url" in summary
        assert "timeout" in summary
        assert "rate_limit" in summary
        assert "enabled_tools" in summary
        assert "total_tools" in summary

        assert summary["environment"] == "sandbox"
        assert summary["total_tools"] == 4
        assert len(summary["enabled_tools"]) == 4

    def test_get_configuration_summary_restricted(self, restricted_config):
        """Test configuration summary with restricted tools."""
        toolkit = JustiFiToolkit(config=restricted_config)
        summary = toolkit.get_configuration_summary()

        assert summary["total_tools"] == 2
        assert len(summary["enabled_tools"]) == 2
        assert "retrieve_payout" in summary["enabled_tools"]
        assert "list_payouts" in summary["enabled_tools"]


class TestToolkitLangChainIntegration:
    """Test LangChain framework integration."""

    def test_langchain_tools_creation(self, basic_config):
        """Test that LangChain tools are created successfully."""
        pytest.importorskip("langchain_core")

        toolkit = JustiFiToolkit(config=basic_config)
        langchain_tools = toolkit.get_langchain_tools()

        # Should have 4 enabled tools
        assert len(langchain_tools) == 4

        # Check tool names
        tool_names = [tool.name for tool in langchain_tools]
        assert "retrieve_payout" in tool_names
        assert "list_payouts" in tool_names
        assert "get_payout_status" in tool_names
        assert "get_recent_payouts" in tool_names

    def test_langchain_tools_with_disabled_tools(self):
        """Test LangChain tools with some tools disabled."""
        pytest.importorskip("langchain_core")

        # Create config with only some tools enabled
        restricted_config = JustiFiConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            enabled_tools=["retrieve_payout", "list_payouts", "get_payout_status"],
        )

        toolkit = JustiFiToolkit(config=restricted_config)
        langchain_tools = toolkit.get_langchain_tools()

        # Should have 3 enabled tools
        assert len(langchain_tools) == 3

        tool_names = [tool.name for tool in langchain_tools]
        assert "retrieve_payout" in tool_names
        assert "list_payouts" in tool_names
        assert "get_payout_status" in tool_names
        assert "get_recent_payouts" not in tool_names

    def test_langchain_tool_schemas(self, basic_config):
        """Test that LangChain tools have proper schemas."""
        pytest.importorskip("langchain_core")

        toolkit = JustiFiToolkit(config=basic_config)
        langchain_tools = toolkit.get_langchain_tools()

        # Find retrieve_payout tool
        retrieve_tool = next(
            tool for tool in langchain_tools if tool.name == "retrieve_payout"
        )

        # Check schema properties
        schema = retrieve_tool.args_schema.schema()
        assert "payout_id" in schema["properties"]
        assert schema["properties"]["payout_id"]["type"] == "string"
        assert "required" in schema
        assert "payout_id" in schema["required"]

    def test_langchain_import_error_handling(self, basic_config):
        """Test graceful handling when LangChain is not installed."""
        toolkit = JustiFiToolkit(config=basic_config)

        # Mock the LangChain adapter import specifically
        with (
            patch("justifi_mcp.adapters.langchain.LangChainAdapter") as mock_adapter,
            pytest.raises(ImportError, match="LangChain is required"),
        ):
            # Make the adapter constructor raise ImportError
            mock_adapter.side_effect = ImportError(
                "LangChain is required for LangChainAdapter. Install with: pip install langchain-core"
            )
            toolkit.get_langchain_tools()

    @pytest.mark.asyncio
    async def test_langchain_tool_execution(self, basic_config, mock_token_response):
        """Test that LangChain tools can be executed (with mocked responses)."""
        pytest.importorskip("langchain_core")

        toolkit = JustiFiToolkit(config=basic_config)
        langchain_tools = toolkit.get_langchain_tools()

        # Find retrieve_payout tool
        retrieve_tool = next(
            tool for tool in langchain_tools if tool.name == "retrieve_payout"
        )

        # Mock the client request
        with respx.mock:
            # Mock OAuth token request
            respx.post("https://api.justifi.ai/v1/oauth/token").mock(
                return_value=Response(200, json=mock_token_response)
            )

            mock_response = {
                "id": "po_test123",
                "status": "paid",
                "amount": 1000,
                "currency": "USD",
            }
            respx.get("https://api.justifi.ai/v1/payouts/po_test123").mock(
                return_value=Response(200, json=mock_response)
            )

            # Execute the tool
            result = await retrieve_tool.arun({"payout_id": "po_test123"})

            # LangChain tools return JSON strings, so parse and compare
            import json

            parsed_result = json.loads(result)
            assert parsed_result == mock_response


class TestToolkitIntegration:
    """Test toolkit integration scenarios."""

    @respx.mock
    async def test_full_workflow(self, basic_config, mock_token_response):
        """Test a complete workflow with the toolkit."""
        # Mock OAuth token request
        respx.post("https://api.justifi.ai/v1/oauth/token").mock(
            return_value=Response(200, json=mock_token_response)
        )

        # Mock payouts list
        mock_payouts_list = {
            "data": [
                {"id": "po_test123", "status": "completed"},
                {"id": "po_test456", "status": "pending"},
            ],
            "has_more": False,
        }
        respx.get("https://api.justifi.ai/v1/payouts").mock(
            return_value=Response(200, json=mock_payouts_list)
        )

        toolkit = JustiFiToolkit(config=basic_config)

        # Get configuration summary
        summary = toolkit.get_configuration_summary()
        assert summary["total_tools"] == 4

        # List tools
        schemas = toolkit.get_tool_schemas()
        assert len(schemas) == 4

        # Execute tool
        result = await toolkit.call_tool("list_payouts", {"limit": 10})
        assert len(result) == 1

        # Check that response includes success indicator and contains the data
        response_text = result[0].text
        assert "✅ Success:" in response_text
        assert "po_test123" in response_text
        assert "po_test456" in response_text

        # Extract JSON from the formatted response
        json_start = response_text.find("{")
        json_part = response_text[json_start:]
        response_data = json.loads(json_part)
        assert len(response_data["data"]) == 2
        assert response_data["data"][0]["id"] == "po_test123"

    def test_environment_specific_configuration(self):
        """Test environment-specific configuration scenarios."""
        # Production configuration - only allow read operations
        prod_config = JustiFiConfig(
            client_id="prod_id",
            client_secret="prod_secret",
            enabled_tools=[
                "retrieve_payout",
                "list_payouts",
                "get_payout_status",
            ],  # Exclude recent for security
            context={
                "environment": "production",
                "timeout": 10,  # Shorter timeout
                "rate_limit": "premium",
            },
        )

        toolkit = JustiFiToolkit(config=prod_config)
        summary = toolkit.get_configuration_summary()

        assert summary["environment"] == "production"
        assert summary["timeout"] == 10
        assert summary["total_tools"] == 3  # recent disabled
        assert "get_recent_payouts" not in summary["enabled_tools"]
