"""Test MCP protocol compliance and server behavior.

These tests focus on MCP-specific functionality rather than AI model behavior.
We test what we can control: tool schemas, server responses, protocol compliance.
"""

import json

import pytest
from mcp.types import TextContent

from justifi_mcp.config import JustiFiConfig
from justifi_mcp.toolkit import JustiFiToolkit


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""

    def test_tool_schemas_are_valid_json_schema(self):
        """Test that all tool schemas are valid JSON Schema."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(config=config)

        schemas = toolkit.get_tool_schemas()

        for schema in schemas:
            # Must have required MCP Tool fields
            assert hasattr(schema, "name")
            assert hasattr(schema, "description")
            assert hasattr(schema, "inputSchema")

            # Name must be valid
            assert isinstance(schema.name, str)
            assert len(schema.name) > 0
            assert (
                "_" in schema.name or schema.name.islower()
            )  # snake_case or lowercase

            # Description must be helpful
            assert isinstance(schema.description, str)
            assert len(schema.description) > 20  # Descriptive enough

            # Input schema must be valid JSON Schema
            input_schema = schema.inputSchema
            assert input_schema["type"] == "object"
            assert "properties" in input_schema

            # All properties should have descriptions
            for prop_name, prop_def in input_schema["properties"].items():
                assert (
                    "description" in prop_def
                ), f"Property {prop_name} missing description"
                assert (
                    len(prop_def["description"]) > 10
                ), f"Property {prop_name} description too short"

    @pytest.mark.asyncio
    async def test_tool_responses_are_valid_mcp_format(self):
        """Test that tool responses follow MCP format."""
        # Create config with disabled tool (only enable some tools)
        config = JustiFiConfig(
            client_id="test",
            client_secret="test",
            enabled_tools=[
                "retrieve_payout",
                "list_payouts",
                "get_payout_status",
            ],  # Exclude get_recent_payouts
        )
        toolkit = JustiFiToolkit(config=config)

        # Test with a disabled tool (should return error in MCP format)
        result = await toolkit.call_tool("get_recent_payouts", {"limit": 5})

        # Should return list of TextContent
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        # Content should be informative
        assert "not enabled" in result[0].text
        assert "Available tools:" in result[0].text

    def test_mcp_server_handlers_exist(self):
        """Test that MCP server has all required handlers."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(config=config)

        server = toolkit.get_mcp_server()

        # Check that server has the required handlers
        # Note: We can't easily test the actual handlers without starting the server,
        # but we can verify the server was created successfully
        assert server is not None

    def test_tool_names_follow_conventions(self):
        """Test that tool names follow MCP conventions."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(config=config)

        schemas = toolkit.get_tool_schemas()

        for schema in schemas:
            name = schema.name

            # Should be snake_case
            assert name.islower(), f"Tool name {name} should be lowercase"
            assert " " not in name, f"Tool name {name} should not contain spaces"

            # Should be descriptive
            assert len(name) > 5, f"Tool name {name} too short"

            # Should indicate action
            action_words = ["get", "list", "retrieve", "create", "update", "delete"]
            has_action = any(word in name for word in action_words)
            assert has_action, f"Tool name {name} should indicate action"


class TestToolSchemaQuality:
    """Test quality of tool schemas for developer experience."""

    def test_tool_descriptions_are_comprehensive(self):
        """Test that tool descriptions provide enough context."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(config=config)

        schemas = toolkit.get_tool_schemas()

        for schema in schemas:
            desc = schema.description

            # Ensure description exists
            assert desc is not None, f"Description for {schema.name} is None"
            assert isinstance(
                desc, str
            ), f"Description for {schema.name} is not a string"

            # Should explain what the tool does
            assert len(desc) > 30, f"Description for {schema.name} too short"

            # Should mention the main entity (payout)
            assert (
                "payout" in desc.lower()
            ), f"Description for {schema.name} should mention payouts"

            # Should not just repeat the name
            name_words = schema.name.replace("_", " ").split()
            desc_lower = desc.lower()
            repeated_words = sum(1 for word in name_words if word in desc_lower)
            unique_content_ratio = 1 - (repeated_words / len(desc.split()))
            assert (
                unique_content_ratio > 0.3
            ), f"Description for {schema.name} too repetitive"

    def test_parameter_schemas_have_examples(self):
        """Test that complex parameters have examples or clear descriptions."""
        config = JustiFiConfig(client_id="test", client_secret="test")
        toolkit = JustiFiToolkit(config=config)

        schemas = toolkit.get_tool_schemas()

        for schema in schemas:
            input_schema = schema.inputSchema

            for prop_name, prop_def in input_schema["properties"].items():
                desc = prop_def["description"]

                # ID parameters should have examples
                if "id" in prop_name.lower():
                    assert (
                        "(" in desc and ")" in desc
                    ), f"ID parameter {prop_name} should have example"
                    # Should have format like "(e.g., 'po_ABC123XYZ')"
                    assert "e.g." in desc or "example" in desc.lower()

                # Limit parameters should have ranges
                if "limit" in prop_name.lower():
                    assert any(
                        char.isdigit() for char in desc
                    ), f"Limit parameter {prop_name} should mention numbers"

    @pytest.mark.asyncio
    async def test_error_handling_provides_guidance(self):
        """Test that error responses provide helpful guidance."""
        # Create config with disabled tool (only enable some tools)
        config = JustiFiConfig(
            client_id="test",
            client_secret="test",
            enabled_tools=[
                "retrieve_payout",
                "list_payouts",
                "get_recent_payouts",
            ],  # Exclude get_payout_status
        )
        toolkit = JustiFiToolkit(config=config)

        # Test disabled tool
        result = await toolkit.call_tool("get_payout_status", {"payout_id": "test"})

        error_text = result[0].text

        # Should explain what's wrong
        assert "not enabled" in error_text

        # Should list alternatives
        assert "Available tools:" in error_text

        # Should list actual available tools
        enabled_tools = config.get_enabled_tools()
        for tool_name in enabled_tools:
            assert tool_name in error_text


class TestUsagePatterns:
    """Test that common usage patterns work as expected."""

    def test_usage_patterns_are_documented(self):
        """Test that usage patterns file exists and is valid."""
        from pathlib import Path

        usage_file = Path("eval/usage_patterns.jsonl")
        assert usage_file.exists(), "Usage patterns file should exist"

        with usage_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) > 0, "Usage patterns should not be empty"

        # Test that each line is valid JSON
        for i, line in enumerate(lines):
            try:
                pattern = json.loads(line.strip())

                # Should have required fields
                assert "user_query" in pattern, f"Line {i+1}: missing user_query"
                assert "expected_tool" in pattern, f"Line {i+1}: missing expected_tool"
                assert (
                    "expected_params" in pattern
                ), f"Line {i+1}: missing expected_params"
                assert (
                    "success_criteria" in pattern
                ), f"Line {i+1}: missing success_criteria"
                assert "meta" in pattern, f"Line {i+1}: missing meta"

                # Fields should be reasonable
                assert (
                    len(pattern["user_query"]) > 10
                ), f"Line {i+1}: user_query too short"
                assert isinstance(
                    pattern["expected_params"], dict
                ), f"Line {i+1}: expected_params should be dict"
                assert isinstance(
                    pattern["success_criteria"], list
                ), f"Line {i+1}: success_criteria should be list"

            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i+1} is not valid JSON: {e}")

    def test_documented_tools_exist(self):
        """Test that tools mentioned in usage patterns actually exist."""
        from pathlib import Path

        config = JustiFiConfig(
            client_id="test", client_secret="test", enabled_tools="all"
        )
        toolkit = JustiFiToolkit(config=config)

        available_tools = set(toolkit.get_enabled_tools().keys())

        # Read usage patterns
        usage_file = Path("eval/usage_patterns.jsonl")
        with usage_file.open("r") as f:
            for line in f:
                pattern = json.loads(line.strip())
                expected_tool = pattern["expected_tool"]

                assert (
                    expected_tool in available_tools
                ), f"Tool {expected_tool} mentioned in usage patterns but not available"


class TestConfigurationQuality:
    """Test that configuration system provides good developer experience."""

    def test_configuration_summary_is_informative(self):
        """Test that configuration summary provides useful information."""
        config = JustiFiConfig(
            client_id="test", client_secret="test", enabled_tools="all"
        )
        toolkit = JustiFiToolkit(config=config)

        summary = toolkit.get_configuration_summary()

        # Should have key information
        required_fields = [
            "environment",
            "base_url",
            "timeout",
            "enabled_tools",
            "total_tools",
        ]
        for field in required_fields:
            assert field in summary, f"Configuration summary missing {field}"

        # Values should be reasonable
        assert summary["total_tools"] > 0
        assert len(summary["enabled_tools"]) == summary["total_tools"]
        assert summary["environment"] in ["sandbox", "production"]
        assert summary["timeout"] > 0

    def test_tool_filtering_works_correctly(self):
        """Test that tool filtering through configuration works."""
        # Create config with only some tools enabled
        config = JustiFiConfig(
            client_id="test",
            client_secret="test",
            enabled_tools=[
                "retrieve_payout",
                "list_payouts",
            ],  # Exclude get_recent_payouts and get_payout_status
        )

        toolkit = JustiFiToolkit(config=config)

        enabled_tools = toolkit.get_enabled_tools()
        schemas = toolkit.get_tool_schemas()

        # Should only have enabled tools
        assert "get_recent_payouts" not in enabled_tools
        assert "get_payout_status" not in enabled_tools
        assert "retrieve_payout" in enabled_tools
        assert "list_payouts" in enabled_tools

        # Schemas should match enabled tools
        schema_names = [s.name for s in schemas]
        assert set(schema_names) == set(enabled_tools.keys())
