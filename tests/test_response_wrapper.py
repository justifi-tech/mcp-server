"""Tests for the response wrapper utility."""

import pytest

from python.tools.response_wrapper import wrap_tool_call


@pytest.mark.asyncio
async def test_wrap_tool_call():
    """Test that wrap_tool_call properly standardizes responses."""
    
    # Test regular tool response
    async def mock_list_payouts(*args, **kwargs):
        return {
            "data": [{"id": "po_123", "status": "completed"}],
            "page_info": {"has_next": False}
        }
    
    result = await wrap_tool_call("list_payouts", mock_list_payouts)
    assert result["metadata"]["tool"] == "list_payouts"
    assert result["metadata"]["type"] == "payouts"
    assert result["data"] == [{"id": "po_123", "status": "completed"}]
    
    # Test special case for get_payout_status
    async def mock_get_status(*args, **kwargs):
        return "completed"
    
    status_result = await wrap_tool_call("get_payout_status", mock_get_status)
    assert status_result["metadata"]["tool"] == "get_payout_status"
    assert status_result["data"] == [{"status": "completed"}]