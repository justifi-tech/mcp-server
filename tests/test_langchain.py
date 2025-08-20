"""Test LangChain adapter integration with auto-generated schemas."""

import pytest

from python.adapters.langchain import LangChainAdapter
from python.config import JustiFiConfig


class TestLangChainAdapterAutoGeneration:
    """Test LangChain adapter with auto-generated schemas."""

    @pytest.fixture
    def basic_config(self):
        """Basic test configuration."""
        return JustiFiConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            enabled_tools=["retrieve_payout", "list_payments"],
        )

    @pytest.fixture
    def all_tools_config(self):
        """Configuration with all tools enabled."""
        return JustiFiConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            enabled_tools="all",
        )

    def test_auto_generated_schemas_match_tools(self, basic_config):
        """Test that auto-generated schemas match enabled tools."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()

        # Should have schemas for enabled tools
        assert len(schemas) == 2
        schema_names = [s["name"] for s in schemas]
        assert "retrieve_payout" in schema_names
        assert "list_payments" in schema_names

    def test_generated_schema_structure(self, basic_config):
        """Test that generated schemas have correct LangChain structure."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()
        schema = next(s for s in schemas if s["name"] == "retrieve_payout")

        # Should have required LangChain fields
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            assert field in schema

        # Parameters should be valid JSON Schema
        params = schema["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        # Should have framework metadata
        assert schema["framework"] == "langchain"

    def test_schema_excludes_client_parameter(self, basic_config):
        """Test that generated schemas exclude the client parameter."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()

        for schema in schemas:
            properties = schema["parameters"]["properties"]
            assert "client" not in properties, f"Found client param in {schema['name']}"

    def test_schema_includes_correct_parameters(self, basic_config):
        """Test that schemas include the correct parameters."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()
        retrieve_payout_schema = next(
            s for s in schemas if s["name"] == "retrieve_payout"
        )

        # retrieve_payout should have payout_id parameter
        properties = retrieve_payout_schema["parameters"]["properties"]
        assert "payout_id" in properties

        # payout_id should be required
        required = retrieve_payout_schema["parameters"]["required"]
        assert "payout_id" in required

        # Should have description
        assert "description" in properties["payout_id"]

    def test_schema_handles_optional_parameters(self, basic_config):
        """Test that schemas correctly handle optional parameters."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()
        list_payments_schema = next(s for s in schemas if s["name"] == "list_payments")

        properties = list_payments_schema["parameters"]["properties"]
        required = list_payments_schema["parameters"]["required"]

        # list_payments has optional parameters
        assert "limit" in properties
        assert "after_cursor" in properties
        assert "before_cursor" in properties

        # Optional parameters should not be in required list
        assert "limit" not in required
        assert "after_cursor" not in required
        assert "before_cursor" not in required

    def test_langchain_tool_creation_with_auto_generation(self):
        """Test that LangChain StructuredTool creation works with auto-generated schemas."""
        pytest.importorskip("langchain_core")
        pytest.importorskip("pydantic")

        config = JustiFiConfig(
            client_id="test", client_secret="test", enabled_tools=["retrieve_payout"]
        )
        adapter = LangChainAdapter(config)

        tools = adapter.get_langchain_tools()

        assert len(tools) == 1
        tool = tools[0]

        # Should be a StructuredTool
        from langchain_core.tools import StructuredTool

        assert isinstance(tool, StructuredTool)
        assert tool.name == "retrieve_payout"
        assert len(tool.description) > 0

        # Should have correct args schema
        assert tool.args_schema is not None

        # Tool should be callable (has coroutine)
        assert hasattr(tool, "coroutine")
        assert tool.coroutine is not None

    def test_all_tools_generate_valid_schemas(self, all_tools_config):
        """Test that all available tools can generate valid schemas."""
        adapter = LangChainAdapter(all_tools_config)

        schemas = adapter.get_tool_schemas()

        # Should have schemas for all available tools
        available_tools = all_tools_config.get_available_tools()
        assert len(schemas) == len(available_tools)

        # All schemas should be valid
        for schema in schemas:
            # Basic structure
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            assert "framework" in schema

            # Parameters structure
            params = schema["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params
            assert isinstance(params["properties"], dict)
            assert isinstance(params["required"], list)

            # No client parameter should be present
            assert "client" not in params["properties"]

    def test_schema_descriptions_from_docstrings(self, basic_config):
        """Test that schema descriptions come from function docstrings."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()
        retrieve_payout_schema = next(
            s for s in schemas if s["name"] == "retrieve_payout"
        )

        # Description should be meaningful (from docstring)
        description = retrieve_payout_schema["description"]
        assert len(description) > 10
        assert "payout" in description.lower()

        # Parameter descriptions should also be meaningful
        payout_id_desc = retrieve_payout_schema["parameters"]["properties"][
            "payout_id"
        ]["description"]
        assert len(payout_id_desc) > 5
        assert "payout" in payout_id_desc.lower() or "id" in payout_id_desc.lower()

    def test_schema_type_conversion(self, basic_config):
        """Test that parameter types are correctly converted."""
        adapter = LangChainAdapter(basic_config)

        schemas = adapter.get_tool_schemas()

        for schema in schemas:
            properties = schema["parameters"]["properties"]

            for _param_name, param_def in properties.items():
                # All parameters should have a valid JSON Schema type
                assert "type" in param_def
                valid_types = [
                    "string",
                    "integer",
                    "number",
                    "boolean",
                    "array",
                    "object",
                    "null",
                ]
                assert param_def["type"] in valid_types

    def test_backward_compatibility_maintained(self, basic_config):
        """Test that the adapter still works with existing functionality."""
        adapter = LangChainAdapter(basic_config)

        # Should still be able to execute tools
        assert hasattr(adapter, "execute_tool")

        # Should still have the same interface
        assert hasattr(adapter, "get_langchain_tools")
        assert hasattr(adapter, "get_tool_schemas")

        # Config should work the same way
        enabled_tools = adapter.config.get_enabled_tools()
        assert len(enabled_tools) == 2
        assert "retrieve_payout" in enabled_tools
