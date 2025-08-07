# Standardized JustiFi API Response Format

This document describes the standardized response format implementation for JustiFi MCP tools.

## Overview

The JustiFi MCP server now uses a standardized response format across all tools by default. This addresses the issue where different tools returned inconsistent field structures, making it difficult for consuming applications to handle responses uniformly.

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

Standardized responses are now enabled by default across all tools. No configuration is needed.

### Legacy Functions (Backward Compatibility)
The following functions are maintained for backward compatibility but have no effect:

```python
from python.tools.response_wrapper import set_standardization_enabled, is_standardization_enabled

# These functions exist for backward compatibility
set_standardization_enabled(True)  # No effect - always enabled
print(is_standardization_enabled())  # Always returns True
```

## Benefits

1. **Consistent Integration**: Consuming applications can always expect `response.data` to contain the records
2. **Simplified Agent Logic**: No need for tool-specific response parsing
3. **Better Maintainability**: Changes to individual tools don't break consuming code
4. **Scalability**: New tools automatically follow the same pattern
5. **Backward Compatibility**: Existing consumers continue to work when disabled

## Implementation Details

### Response Normalization
The system detects and handles different response patterns:

1. **Standard JustiFi API format**: `{"data": [...], "page_info": {...}}`
2. **Custom formats**: Like `get_recent_payouts` returning `{"payouts": [...], "count": N}`
3. **Single item responses**: From retrieve operations
4. **Unknown formats**: Intelligent extraction with warnings

### Tool Integration
The MCP server uses a wrapper system that conditionally applies standardization:

```python
# In the MCP server
return await wrap_tool_call("list_payouts", _list_payouts, client, limit)
```

When standardization is disabled, tools return their original response format.

### Data Type Detection
The system automatically maps tool names to data types:
- `list_payouts` → `"payouts"`
- `retrieve_payment` → `"payment"`
- `get_recent_payouts` → `"payouts"`

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

## Migration Guide

### For New Applications
Simply enable standardization and use the `data` field for all responses:

```python
set_standardization_enabled(True)
result = await some_tool(...)
records = result["data"]  # Always a list
```

### For Existing Applications
The feature is backward compatible. Existing code continues to work when standardization is disabled (default).

To migrate gradually:
1. Test with standardization enabled in development
2. Update code to use `response["data"]` instead of tool-specific fields
3. Enable in production once migration is complete

## File Structure

### Core Implementation
- `python/tools/response_formatter.py` - Core standardization logic
- `python/tools/response_wrapper.py` - Optional wrapper system
- `modelcontextprotocol/server.py` - MCP server integration

### Tests
- `tests/test_response_formatter.py` - Response formatter tests
- `tests/test_response_wrapper.py` - Wrapper system tests

### Tool Updates
- `python/tools/payouts.py` - Added standardized versions
- `python/tools/payments.py` - Added standardized versions
- `python/tools/__init__.py` - Export new functions

## Future Enhancements

1. **Configuration per tool**: Enable standardization for specific tools only
2. **Response versioning**: Support multiple response format versions
3. **Schema validation**: Validate standardized responses against schemas
4. **Performance optimization**: Cache standardization decisions