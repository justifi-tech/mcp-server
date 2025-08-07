# Standardized JustiFi API Response Format

This document describes the standardized response format implementation for JustiFi MCP tools.

## Overview

The JustiFi MCP server uses a standardized response format across all 21 tools by default. This addresses the issue where different tools returned inconsistent field structures, making it difficult for consuming applications to handle responses uniformly.

**Current Status**: Standardized responses are always enabled for all tools. Legacy backward compatibility code has been removed.

## Response Format

All tools now return responses in this standardized format:

```json
{
  "data": [...],           // Always contains the actual records
  "metadata": {
    "type": "payouts",     // Indicates what type of data
    "count": 5,            // Number of records
    "tool": "get_recent_payouts", // Source tool name
    "original_format": "custom", // Original response format
    "is_single_item": false // For retrieve operations
  },
  "page_info": {...}       // Pagination info if applicable
}
```

## Configuration

Standardized responses are always enabled across all 21 tools. No configuration is needed or available - the format is mandatory for consistency.

All tools use the `wrap_tool_call()` function from `python.tools.response_wrapper` to ensure standardized responses.

## Benefits

1. **Consistent Integration**: Consuming applications can always expect `response.data` to contain the records
2. **Simplified Agent Logic**: No need for tool-specific response parsing
3. **Better Maintainability**: Changes to individual tools don't break consuming code
4. **Scalability**: New tools automatically follow the same pattern
5. **Universal Coverage**: All 21 tools follow the same response structure

## Implementation Details

### Response Normalization
The system detects and handles different response patterns:

1. **Standard JustiFi API format**: `{"data": [...], "page_info": {...}}`
2. **Custom formats**: Like `get_recent_payouts` returning `{"payouts": [...], "count": N}`
3. **Single item responses**: From retrieve operations
4. **Unknown formats**: Intelligent extraction with warnings

### Tool Integration
The MCP server uses a universal wrapper system that applies standardization to all tools:

```python
# In the MCP server
return await wrap_tool_call("list_payouts", _list_payouts, client, limit)
```

All tools are automatically wrapped with this system - there is no way to disable standardization.

### Data Type Detection
The system automatically maps tool names to data types for all 21 tools:
- `list_payouts` → `"payouts"`
- `retrieve_payment` → `"payment"`  
- `get_recent_payouts` → `"payouts"`
- `list_disputes` → `"disputes"`
- `retrieve_dispute` → `"dispute"`
- `list_checkouts` → `"checkouts"`
- `retrieve_checkout` → `"checkout"`
- `list_balance_transactions` → `"balance_transactions"`
- `retrieve_balance_transaction` → `"balance_transaction"`
- `list_refunds` → `"refunds"`
- `retrieve_refund` → `"refund"`
- `list_payment_refunds` → `"refunds"`
- `retrieve_payment_method` → `"payment_method"`
- `list_sub_accounts` → `"sub_accounts"`
- `get_sub_account` → `"sub_account"`
- `get_sub_account_payout_account` → `"sub_account_payout_account"`
- `get_sub_account_settings` → `"sub_account_settings"`
- `get_payout_status` → `"payout_status"`

### Utility Functions
Helper functions are available for working with standardized responses:

```python
from python.tools.response_formatter import (
    get_raw_data,
    get_single_item,
    is_single_item_response
)

# Extract raw data from standardized response
data = get_raw_data(standardized_response)

# Check if response represents a single item
if is_single_item_response(standardized_response):
    item = get_single_item(standardized_response)
```

## Examples

### Original vs. Standardized Responses

**get_recent_payouts (Custom Format)**
```json
// Original
{
  "payouts": [{"id": "po_123", "status": "completed"}],
  "count": 1,
  "limit": 10
}

// Standardized
{
  "data": [{"id": "po_123", "status": "completed"}],
  "metadata": {
    "type": "payouts",
    "count": 1,
    "tool": "get_recent_payouts",
    "original_format": "custom",
    "limit": 10
  }
}
```

**list_payments (API Format)**
```json
// Original
{
  "data": [{"id": "py_456", "status": "succeeded"}],
  "page_info": {"has_next": false}
}

// Standardized
{
  "data": [{"id": "py_456", "status": "succeeded"}],
  "metadata": {
    "type": "payments",
    "count": 1,
    "tool": "list_payments",
    "original_format": "api"
  },
  "page_info": {"has_next": false}
}
```

**retrieve_payout (Single Item)**
```json
// Original
{
  "data": {"id": "po_123", "status": "completed"}
}

// Standardized
{
  "data": [{"id": "po_123", "status": "completed"}],
  "metadata": {
    "type": "payout",
    "count": 1,
    "tool": "retrieve_payout",
    "original_format": "api",
    "is_single_item": true
  }
}
```

## Usage Guide

### Working with Standardized Responses
All applications should use the `data` field for accessing records:

```python
# All tools return standardized responses
result = await some_tool(...)
records = result["data"]  # Always a list
metadata = result["metadata"]  # Tool info and type detection
page_info = result.get("page_info")  # Pagination if applicable
```

### Single Item vs List Responses
Use the `is_single_item` metadata field to determine response type:

```python
if result["metadata"]["is_single_item"]:
    # Retrieve operations - single item wrapped in array
    item = result["data"][0]
else:
    # List operations - multiple items
    items = result["data"]
```

## File Structure

### Core Implementation
- `python/tools/response_formatter.py` - Core standardization logic
- `python/tools/response_wrapper.py` - Universal wrapper system with `wrap_tool_call()`
- `modelcontextprotocol/server.py` - MCP server integration for all 21 tools

### Tests
- `tests/test_response_formatter.py` - Response formatter tests
- `tests/test_response_wrapper.py` - Wrapper system tests

### Tool Integration
- All tools in `python/tools/` directory use the wrapper system
- `python/tools/__init__.py` - Exports wrapper functions
- Individual tool files (payouts.py, payments.py, etc.) - Core implementations wrapped by MCP server

## Future Enhancements

1. **Response versioning**: Support multiple response format versions
2. **Schema validation**: Validate standardized responses against schemas  
3. **Performance optimization**: Cache standardization decisions
4. **Extended metadata**: Add more context about data transformations