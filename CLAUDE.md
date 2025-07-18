# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **JustiFi MCP (Model Context Protocol) server** for AI-assisted payment management. It provides comprehensive payment tools through the JustiFi API and supports multiple AI frameworks including Claude Desktop, Cursor IDE, LangChain, and OpenAI.

## Architecture

### Core Components

**MCP Server Structure:**
- `main.py` - Entry point that delegates to `modelcontextprotocol/main.py`
- `modelcontextprotocol/` - FastMCP server implementation with all tool registrations
- `python/` - Core business logic and tools
  - `core.py` - JustiFi API client with OAuth2 authentication
  - `tools/` - Payment operation tools (payments, payouts, refunds, etc.)
  - `adapters/` - Framework adapters (LangChain)
  - `config.py` - Configuration management
  - `toolkit.py` - Multi-framework toolkit interface

**Tool Categories:**
- **Payment Tools**: retrieve_payment, list_payments  
- **Payout Tools**: retrieve_payout, list_payouts, get_payout_status, get_recent_payouts
- **Refund Tools**: retrieve_refund, list_refunds, list_payment_refunds
- **Balance Tools**: list_balance_transactions, retrieve_balance_transaction
- **Dispute Tools**: list_disputes, retrieve_dispute
- **Checkout Tools**: list_checkouts, retrieve_checkout
- **Payment Method Tools**: retrieve_payment_method

### Authentication Flow

The server uses OAuth2 Client-Credentials flow with automatic token management:
- Tokens are cached and automatically refreshed
- 401 responses trigger token refresh and retry
- All credentials are managed via environment variables

## Development Commands

**Local Development with uv:**

```bash
# Set up development environment
make setup

# Start MCP server with auto-restart
make dev

# Run all tests
make test

# Code quality checks
make lint
make format
make check-all

# Interactive development shell
make shell
```

**Individual Test Files:**
```bash
uv run pytest tests/test_payout_tools.py -v
uv run pytest tests/test_payment_tools.py -v
uv run pytest tests/test_main.py -v
```

**API Drift Monitoring:**
```bash
make drift-check
```

## Configuration

### Environment Variables (Required)

```bash
JUSTIFI_CLIENT_ID=your_client_id
JUSTIFI_CLIENT_SECRET=your_client_secret
```

### Tool Configuration (Security by Default)

```bash
# Default: No tools enabled - must explicitly enable
JUSTIFI_ENABLED_TOOLS=all                                    # Enable all tools
JUSTIFI_ENABLED_TOOLS="retrieve_payout,list_payouts"         # Enable specific tools
JUSTIFI_ENABLED_TOOLS="retrieve_payout,get_payout_status"    # Custom combination
```

### Transport Options

```bash
# Stdio (default - for local AI clients)
python main.py

# HTTP (for web-based clients)
MCP_TRANSPORT=http MCP_PORT=3000 python main.py

# Server-Sent Events
MCP_TRANSPORT=sse MCP_PORT=3000 python main.py
```

## Framework Integration

### MCP Client Configuration

**Cursor IDE** (`cursor_mcp_config.json`):
```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/mcp-servers"
    }
  }
}
```

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["/path/to/mcp-servers/main.py"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret",
        "JUSTIFI_ENABLED_TOOLS": "all"
      }
    }
  }
}
```

### Multi-Framework Support

**LangChain Integration:**
```python
from python.adapters.langchain import JustiFiLangChainAdapter
from python.config import JustiFiConfig

config = JustiFiConfig(client_id="...", client_secret="...")
adapter = JustiFiLangChainAdapter(config)
tools = adapter.get_langchain_tools()
```

**OpenAI Integration:**
```python
from python.tools.payments import retrieve_payment
from python.core import JustiFiClient

client = JustiFiClient(client_id="...", client_secret="...")
result = await retrieve_payment(client, "py_ABC123")
```

## Code Standards

### Makefile-First Development

**ALWAYS try Makefile commands first before using direct commands:**

1. **Check available commands**: `make help` or `make` (shows all targets)
2. **Use existing commands**: `make test`, `make lint`, `make format`, `make dev`, etc.
3. **If no Makefile command exists**: Ask if it makes sense to add one to the Makefile
4. **Only use direct commands**: If it's clearly a one-off operation

**Examples:**
- ✅ `make test` instead of `docker-compose run --rm dev pytest tests/ -v`
- ✅ `make lint` instead of `docker-compose run --rm dev ruff check .`
- ✅ `make format` instead of `docker-compose run --rm dev ruff format .`
- ✅ `make dev` instead of `docker-compose up mcp-dev -d`

**When to suggest adding Makefile commands:**
- Commands that will be run repeatedly during development
- Commands that have complex arguments or flags
- Commands that developers need to remember the exact syntax for
- Commands that combine multiple steps

### Development Guidelines

- **All development must use Docker containers** - no local execution
- **Always use `uv` for package management** instead of pip
- **All I/O operations must be async/await**
- **Add `@traceable` decorators to all external API calls**
- **Use type hints for all functions and parameters**

### Error Handling

- Implement comprehensive error handling for all API calls
- Use meaningful error messages that help users understand issues
- Never log sensitive information (API keys, payment details)
- Handle rate limiting and network timeouts gracefully

### Testing Philosophy

**Focus on critical error scenarios only:**
- Authentication failures (OAuth/credential issues)
- Invalid configurations
- Network timeouts and API failures
- Malformed API responses
- Tool execution with invalid inputs
- One success test per tool

**Avoid testing:**
- Constructor parameter variations
- Schema consistency checks
- Getter/setter validation
- Framework adapter creation
- Configuration summary structure

## Security

- All credentials must be environment variables
- Never commit secrets to the repository
- Validate all user inputs before API calls
- Use OAuth2 token caching with secure expiration
- Implement proper error handling without exposing internals

## Troubleshooting

- Check LangSmith traces for debugging tool execution
- Use `make dev` for auto-restart development workflow
- Verify environment variables are loaded correctly
- Check container logs with `make logs`
- All tests should pass - currently 74/74 passing
- Test API connectivity with individual tool tests