"""Tests for the response formatter utility."""

from python.tools.response_formatter import (
    get_raw_data,
    get_single_item,
    is_single_item_response,
    standardize_response,
)


class TestStandardizeResponse:
    """Test the standardize_response function."""

    def test_standardize_api_list_response(self):
        """Test standardizing a typical JustiFi API list response."""
        original_response = {
            "data": [
                {"id": "po_123", "status": "completed"},
                {"id": "po_456", "status": "pending"},
            ],
            "page_info": {
                "has_next": True,
                "has_previous": False,
                "start_cursor": "cursor_start",
                "end_cursor": "cursor_end",
            },
        }

        result = standardize_response(original_response, "list_payouts")

        assert result["data"] == original_response["data"]
        assert result["metadata"]["type"] == "payouts"
        assert result["metadata"]["count"] == 2
        assert result["metadata"]["tool"] == "list_payouts"
        assert result["metadata"]["original_format"] == "api"
        assert result["page_info"] == original_response["page_info"]

    def test_standardize_single_item_response(self):
        """Test standardizing a single item retrieve response."""
        original_response = {
            "data": {"id": "po_123", "status": "completed", "amount": 1000}
        }

        result = standardize_response(original_response, "retrieve_payout")

        # Single items should be wrapped in a list for consistency
        assert result["data"] == [original_response["data"]]
        assert result["metadata"]["type"] == "payout"
        assert result["metadata"]["count"] == 1
        assert result["metadata"]["tool"] == "retrieve_payout"
        assert result["metadata"]["original_format"] == "api"
        assert result["metadata"]["is_single_item"] is True
        assert "page_info" not in result

    def test_standardize_custom_get_recent_payouts_response(self):
        """Test standardizing the custom get_recent_payouts response format."""
        original_response = {
            "payouts": [
                {"id": "po_123", "status": "completed"},
                {"id": "po_456", "status": "pending"},
            ],
            "count": 2,
            "limit": 10,
        }

        result = standardize_response(original_response, "get_recent_payouts")

        assert result["data"] == original_response["payouts"]
        assert result["metadata"]["type"] == "payouts"
        assert result["metadata"]["count"] == 2
        assert result["metadata"]["tool"] == "get_recent_payouts"
        assert result["metadata"]["original_format"] == "custom"
        assert result["metadata"]["limit"] == 10
        assert "page_info" not in result

    def test_standardize_empty_list_response(self):
        """Test standardizing an empty list response."""
        original_response = {"data": [], "page_info": {"has_next": False}}

        result = standardize_response(original_response, "list_payments")

        assert result["data"] == []
        assert result["metadata"]["count"] == 0
        assert result["metadata"]["type"] == "payments"
        assert result["page_info"] == original_response["page_info"]

    def test_standardize_unknown_format(self):
        """Test standardizing a response with unknown format."""
        original_response = {"unknown_field": [{"id": "test_123"}]}

        result = standardize_response(original_response, "unknown_tool")

        # Should attempt to extract data intelligently
        assert result["data"] == [
            original_response
        ]  # Fallback wraps entire response in list
        assert result["metadata"]["type"] == "unknown"
        assert result["metadata"]["tool"] == "unknown_tool"
        assert result["metadata"]["original_format"] == "unknown"
        assert "warning" in result["metadata"]

    def test_data_type_extraction(self):
        """Test that data types are correctly extracted from tool names."""
        test_cases = [
            ("list_payments", "payments"),
            ("retrieve_payment", "payment"),
            ("list_disputes", "disputes"),
            ("get_recent_payouts", "payouts"),
            ("unknown_tool", "unknown"),
        ]

        for tool_name, expected_type in test_cases:
            response = {"data": []}
            result = standardize_response(response, tool_name)
            assert result["metadata"]["type"] == expected_type


class TestUtilityFunctions:
    """Test utility functions for working with standardized responses."""

    def test_get_raw_data(self):
        """Test extracting raw data from standardized response."""
        standardized = {
            "data": [{"id": "po_123"}, {"id": "po_456"}],
            "metadata": {"type": "payouts"},
        }

        raw_data = get_raw_data(standardized)
        assert raw_data == [{"id": "po_123"}, {"id": "po_456"}]

    def test_get_raw_data_empty(self):
        """Test extracting raw data from empty standardized response."""
        standardized = {"data": [], "metadata": {"type": "payouts"}}

        raw_data = get_raw_data(standardized)
        assert raw_data == []

    def test_is_single_item_response_true(self):
        """Test identifying single item responses."""
        standardized = {
            "data": [{"id": "po_123"}],
            "metadata": {"type": "payout", "is_single_item": True},
        }

        assert is_single_item_response(standardized) is True

    def test_is_single_item_response_false(self):
        """Test identifying list responses."""
        standardized = {
            "data": [{"id": "po_123"}, {"id": "po_456"}],
            "metadata": {"type": "payouts"},
        }

        assert is_single_item_response(standardized) is False

    def test_get_single_item_success(self):
        """Test extracting single item from single item response."""
        standardized = {
            "data": [{"id": "po_123", "status": "completed"}],
            "metadata": {"type": "payout", "is_single_item": True},
        }

        item = get_single_item(standardized)
        assert item == {"id": "po_123", "status": "completed"}

    def test_get_single_item_not_single_item(self):
        """Test that get_single_item returns None for list responses."""
        standardized = {
            "data": [{"id": "po_123"}, {"id": "po_456"}],
            "metadata": {"type": "payouts"},
        }

        item = get_single_item(standardized)
        assert item is None

    def test_get_single_item_empty(self):
        """Test that get_single_item returns None for empty single item response."""
        standardized = {
            "data": [],
            "metadata": {"type": "payout", "is_single_item": True},
        }

        item = get_single_item(standardized)
        assert item is None
