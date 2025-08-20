"""Test auto-generated schema functionality."""

from unittest.mock import MagicMock

from python.adapters.schema_generator import (
    convert_python_type_to_json_schema,
    extract_args_from_docstring,
    extract_description,
    extract_function_info,
    generate_langchain_schema,
)


class TestExtractFunctionInfo:
    """Test extraction of function parameter information."""

    def test_extract_function_info_simple_function(self):
        """Test extraction from a simple function."""

        def simple_func(name: str, age: int = 25):
            """A simple function."""
            pass

        info = extract_function_info(simple_func)

        assert "parameters" in info
        assert "name" in info["parameters"]
        assert "age" in info["parameters"]

        name_param = info["parameters"]["name"]
        assert name_param["name"] == "name"
        assert name_param["type"] is str
        assert not name_param["optional"]

        age_param = info["parameters"]["age"]
        assert age_param["name"] == "age"
        assert age_param["type"] is int
        assert age_param["optional"]
        assert age_param["default"] == 25

    def test_extract_function_info_decorated_function(self):
        """Test extraction from decorated function (like our tool functions)."""
        from python.tools.payouts import retrieve_payout

        info = extract_function_info(retrieve_payout)

        assert "parameters" in info
        assert "client" in info["parameters"]
        assert "payout_id" in info["parameters"]

        payout_id_param = info["parameters"]["payout_id"]
        assert payout_id_param["name"] == "payout_id"
        assert payout_id_param["type"] is str
        assert not payout_id_param["optional"]

    def test_extract_function_info_with_optional_params(self):
        """Test extraction with optional parameters."""
        from python.tools.payouts import list_payouts

        info = extract_function_info(list_payouts)

        assert "parameters" in info
        assert "limit" in info["parameters"]
        assert "after_cursor" in info["parameters"]

        limit_param = info["parameters"]["limit"]
        assert limit_param["optional"]
        assert limit_param["default"] == 25

        cursor_param = info["parameters"]["after_cursor"]
        assert cursor_param["optional"]
        assert cursor_param["default"] is None


class TestGenerateLangchainSchema:
    """Test schema generation for LangChain tools."""

    def test_generate_langchain_schema_retrieve_payout(self):
        """Test schema generation for retrieve_payout tool."""
        from python.tools.payouts import retrieve_payout

        schema = generate_langchain_schema("retrieve_payout", retrieve_payout)

        # Should have correct structure
        assert schema["name"] == "retrieve_payout"
        assert "description" in schema
        assert schema["parameters"]["type"] == "object"
        assert "payout_id" in schema["parameters"]["properties"]
        assert "payout_id" in schema["parameters"]["required"]

        # Should not include 'client' parameter
        assert "client" not in schema["parameters"]["properties"]

        # Check payout_id parameter details
        payout_id_prop = schema["parameters"]["properties"]["payout_id"]
        assert payout_id_prop["type"] == "string"
        assert "description" in payout_id_prop

    def test_generate_langchain_schema_list_payouts(self):
        """Test schema generation for list_payouts tool with optional parameters."""
        from python.tools.payouts import list_payouts

        schema = generate_langchain_schema("list_payouts", list_payouts)

        # Should have correct structure
        assert schema["name"] == "list_payouts"
        assert "limit" in schema["parameters"]["properties"]
        assert "after_cursor" in schema["parameters"]["properties"]
        assert "before_cursor" in schema["parameters"]["properties"]

        # Required parameters should not include optional ones
        required = schema["parameters"]["required"]
        assert "limit" not in required
        assert "after_cursor" not in required
        assert "before_cursor" not in required

        # Check limit parameter
        limit_prop = schema["parameters"]["properties"]["limit"]
        assert limit_prop["type"] == "integer"

    def test_generate_langchain_schema_complex_tool(self):
        """Test schema generation for more complex tool."""
        from python.tools.payment_method_groups import create_payment_method_group

        schema = generate_langchain_schema(
            "create_payment_method_group", create_payment_method_group
        )

        assert schema["name"] == "create_payment_method_group"
        assert "name" in schema["parameters"]["properties"]
        assert "description" in schema["parameters"]["properties"]
        assert "payment_method_ids" in schema["parameters"]["properties"]

        # Name should be required
        assert "name" in schema["parameters"]["required"]

        # Description and payment_method_ids should be optional
        assert "description" not in schema["parameters"]["required"]
        assert "payment_method_ids" not in schema["parameters"]["required"]


class TestDocstringParsing:
    """Test docstring parsing for descriptions and parameters."""

    def test_extract_description_simple(self):
        """Test extraction of description from simple docstring."""

        def test_func():
            """Retrieve a payout by its ID."""
            pass

        description = extract_description(test_func)
        assert description == "Retrieve a payout by its ID"

    def test_extract_description_removes_trailing_period(self):
        """Test that trailing periods are removed from descriptions."""

        def test_func():
            """Retrieve a payout by its ID."""
            pass

        description = extract_description(test_func)
        assert description == "Retrieve a payout by its ID"

    def test_extract_description_no_docstring(self):
        """Test extraction when function has no docstring."""

        def test_func():
            pass

        description = extract_description(test_func)
        assert description == "Execute test_func operation"

    def test_extract_args_from_docstring_google_style(self):
        """Test extraction of args from Google-style docstring."""

        def test_func():
            """Test function.

            Args:
                client: JustiFi client instance.
                payout_id: The ID of the payout to retrieve (e.g., 'po_ABC123XYZ').
                limit: Number of payouts to return (default: 25, max: 100).

            Returns:
                JSON response from the JustiFi API with payout details.
            """
            pass

        args = extract_args_from_docstring(test_func)

        assert "client" in args
        assert "payout_id" in args
        assert "limit" in args

        assert args["client"] == "JustiFi client instance."
        assert (
            args["payout_id"]
            == "The ID of the payout to retrieve (e.g., 'po_ABC123XYZ')."
        )
        assert args["limit"] == "Number of payouts to return (default: 25, max: 100)."

    def test_extract_args_from_docstring_real_tool(self):
        """Test extraction from real tool docstring."""
        from python.tools.payouts import retrieve_payout

        args = extract_args_from_docstring(retrieve_payout)

        assert "client" in args
        assert "payout_id" in args

        # Check that descriptions are extracted
        assert len(args["payout_id"]) > 10
        assert "payout" in args["payout_id"].lower()

    def test_extract_args_no_docstring(self):
        """Test extraction when function has no docstring."""

        def test_func():
            pass

        args = extract_args_from_docstring(test_func)
        assert args == {}


class TestTypeConversion:
    """Test Python type to JSON Schema type conversion."""

    def test_convert_basic_types(self):
        """Test conversion of basic Python types."""
        assert convert_python_type_to_json_schema(str) == "string"
        assert convert_python_type_to_json_schema(int) == "integer"
        assert convert_python_type_to_json_schema(float) == "number"
        assert convert_python_type_to_json_schema(bool) == "boolean"
        assert convert_python_type_to_json_schema(list) == "array"
        assert convert_python_type_to_json_schema(dict) == "object"

    def test_convert_none_type(self):
        """Test conversion of None type."""
        assert convert_python_type_to_json_schema(type(None)) == "null"

    def test_convert_string_types(self):
        """Test conversion when type is provided as string."""
        assert convert_python_type_to_json_schema("str") == "string"
        assert convert_python_type_to_json_schema("int") == "integer"
        assert convert_python_type_to_json_schema("float") == "number"

    def test_convert_generic_types(self):
        """Test conversion of generic types like list[str]."""
        # Mock generic types that might come from type hints
        mock_list_type = MagicMock()
        mock_list_type.__str__ = MagicMock(return_value="list[str]")
        assert convert_python_type_to_json_schema(mock_list_type) == "array"

        mock_dict_type = MagicMock()
        mock_dict_type.__str__ = MagicMock(return_value="dict[str, Any]")
        assert convert_python_type_to_json_schema(mock_dict_type) == "object"

    def test_convert_union_types(self):
        """Test conversion of Union types (Optional)."""
        # Mock Union[str, None] type
        mock_optional_str = MagicMock()
        mock_optional_str.__str__ = MagicMock(return_value="Union[str, NoneType]")
        assert convert_python_type_to_json_schema(mock_optional_str) == "string"

    def test_convert_unknown_type(self):
        """Test conversion of unknown types defaults to string."""

        class CustomType:
            pass

        assert convert_python_type_to_json_schema(CustomType) == "string"


class TestIntegrationScenarios:
    """Test integration scenarios that combine multiple components."""

    def test_schema_generation_matches_tool_count(self):
        """Test that we can generate schemas for all available tools."""
        from python.config import JustiFiConfig

        config = JustiFiConfig(client_id="test", client_secret="test")
        available_tools = config.get_available_tools()

        # Import tools module to access functions
        from python import tools

        generated_count = 0
        for tool_name in available_tools:
            tool_func = getattr(tools, tool_name, None)
            if tool_func:
                schema = generate_langchain_schema(tool_name, tool_func)
                assert schema["name"] == tool_name
                assert "description" in schema
                assert "parameters" in schema
                generated_count += 1

        # Should be able to generate schemas for all tools
        assert generated_count == len(available_tools)

    def test_schema_structure_consistency(self):
        """Test that all generated schemas have consistent structure."""
        from python.config import JustiFiConfig

        config = JustiFiConfig(client_id="test", client_secret="test")
        available_tools = list(config.get_available_tools())[:5]  # Test first 5 tools

        from python import tools

        for tool_name in available_tools:
            tool_func = getattr(tools, tool_name)
            schema = generate_langchain_schema(tool_name, tool_func)

            # All schemas should have these required fields
            required_fields = ["name", "description", "parameters"]
            for field in required_fields:
                assert field in schema, f"Missing {field} in {tool_name} schema"

            # Parameters should be valid JSON Schema
            params = schema["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params

            # All parameters should have type and description
            for param_name, param_def in params["properties"].items():
                assert "type" in param_def
                assert "description" in param_def
                assert param_name != "client"  # Should exclude client param
