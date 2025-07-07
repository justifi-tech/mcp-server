# JustiFi MCP Server

A **payout-focused** Model Context Protocol (MCP) server for AI-assisted payment management. This server provides 4 comprehensive tools for payout operations through the JustiFi API.

## 🏗️ MCP Architecture

**This is an MCP SERVER** - it provides JustiFi payment tools to AI applications via the MCP protocol:

```
┌─────────────────┐    MCP Protocol     ┌──────────────────┐    JustiFi API
│   MCP Client    │◄──────────────────►│   MCP Server     │◄─────────────────►
│ (AI App)        │   (JSON-RPC/stdio) │ (This Project)   │   (Payment API)
│                 │                     │                 │
│ • Claude Desktop│                     │ • No AI models  │
│ • Cursor IDE    │                     │ • Only JustiFi  │
│ • Custom Apps   │                     │   credentials   │
│ • LangChain     │                     │ • Tool provider │
└─────────────────┘                     └──────────────────┘
```

**Key Points:**
- ✅ **Server Role**: Provides payment tools, doesn't need AI model credentials
- ✅ **Client Integration**: Works with any MCP client (Claude, Cursor, custom apps)
- ✅ **Clean Separation**: Payment logic (server) vs AI reasoning (clients)
- ✅ **Examples Available**: See [`examples/`](./examples/) for client-side integration patterns

## 🎯 Focus: Payout Operations

This MCP server specializes in payout management with these tools:
- `retrieve_payout` - Get detailed payout information
- `list_payouts` - List payouts with pagination
- `get_payout_status` - Quick status check for payouts
- `get_recent_payouts` - Get the most recent payouts

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- JustiFi API credentials
- Docker (for containerized development)

### Setup
1. **Clone and configure**:
   ```bash
   git clone <repository>
   cd mcp-servers
   cp env.example .env
   # Edit .env with your JustiFi API credentials
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Test the setup**:
   ```bash
   make test-local
   ```

## 🔧 Development Commands

### Local Development (Fastest)
```bash
# Run MCP server locally
make dev-local

# Run tests locally
make test-local
```

### Container Development
```bash
# Start development environment
make dev-start

# Run MCP server with auto-restart in container
make dev

# Interactive shell in container
make shell
```


## 🧪 Testing

### All Tests
```bash
# Run in container (full environment)
make test

# Run locally (faster)
make test-local
```

### Individual Test Classes
```bash
python -m pytest tests/test_payout_tools.py::TestRetrievePayout -v
python -m pytest tests/test_payout_tools.py::TestListPayouts -v
python -m pytest tests/test_payout_tools.py::TestGetPayoutStatus -v
python -m pytest tests/test_payout_tools.py::TestGetRecentPayouts -v
```

## 🔌 MCP Integration

### Cursor IDE
1. Add to your `cursor_mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "justifi-payouts": {
         "command": "python",
         "args": ["main.py"],
         "cwd": "/path/to/mcp-servers"
       }
     }
   }
   ```

### Claude Desktop
1. Add to your MCP settings:
   ```json
   {
     "mcpServers": {
       "justifi-payouts": {
         "command": "python",
         "args": ["/path/to/mcp-servers/main.py"]
       }
     }
   }
   ```

## 🌐 Environment Variables

**MCP Server Requirements (Only JustiFi):**
```bash
JUSTIFI_CLIENT_ID=your_client_id
JUSTIFI_CLIENT_SECRET=your_client_secret
```

Tool Configuration (Security by Default):
```bash
# Default: No tools enabled (secure by default)
# You must explicitly enable tools:

JUSTIFI_ENABLED_TOOLS=all                                    # Enable all tools
JUSTIFI_ENABLED_TOOLS="retrieve_payout,list_payouts"         # Enable specific tools only
JUSTIFI_ENABLED_TOOLS="retrieve_payout,get_payout_status"    # Custom combination
```

Optional:
```bash
JUSTIFI_BASE_URL=https://api.justifi.ai     # Default (no /v1 suffix)
LANGCHAIN_API_KEY=your_langsmith_key        # For tracing/observability
LANGCHAIN_TRACING_V2=true                   # Enable tracing
LOG_LEVEL=INFO                              # DEBUG, INFO, WARNING, ERROR
```

**Note**: No AI model API keys needed! Those are handled by MCP clients, not this server.

## 🔍 Available Tools

### `retrieve_payout`
Get complete payout details by ID.
```json
{
  "payout_id": "po_ABC123XYZ"
}
```

### `list_payouts`
List payouts with cursor-based pagination.
```json
{
  "limit": 25,
  "after_cursor": "optional_cursor"
}
```

### `get_payout_status`
Quick status check (returns just the status string).
```json
{
  "payout_id": "po_ABC123XYZ"
}
```

### `get_recent_payouts`
Get the most recent payouts (optimized for recency).
```json
{
  "limit": 10
}
```

## 🧠 AI Evaluation

Test the MCP server with AI scenarios:
```bash
# Run evaluation suite
make eval

# View evaluation scenarios
cat eval/payout_operations.jsonl
```

## 🔄 API Drift Monitoring

Monitor JustiFi API changes automatically:
```bash
# Check for API changes
make drift-check

# Force update API specification
make drift-update
```

**Configuration**: Set `JUSTIFI_OPENAPI_URL` environment variable with the correct JustiFi OpenAPI specification URL.

**Automation**: GitHub Actions workflow runs weekly to detect API changes and create PRs/issues automatically.

## 🏛️ Architecture

### Clean & Focused
- **Payout specialization**: 4 focused tools vs generic approach
- **Flat package structure**: `justifi_mcp/` (not `src/justifi_mcp/`)
- **Container-first development**: Docker for consistency
- **Comprehensive testing**: 12 tests covering all scenarios

### OAuth2 Flow
- Automatic token acquisition and caching
- 401 retry with token refresh
- Secure credential management

### MCP Compliance
- JSON-RPC 2.0 over stdio transport
- Proper tool schema definitions
- Error handling and validation
- LangSmith tracing support

## 📚 Documentation

- [PRD v2.0](docs/PRD-JustiFi-MCP-v2.0.md) - Strategic roadmap and framework strategy
- [API Endpoint Inventory](docs/endpoint-inventory.md) - Verified JustiFi API endpoints

## 🔌 Framework Integration

### MCP (Model Context Protocol)
- **Primary integration** for IDE usage (Cursor, VS Code, Windsurf)
- Full MCP server with tool schemas and JSON-RPC 2.0 protocol
- See [MCP Integration](#-mcp-integration) section above

### LangChain
- **Dedicated adapter** with StructuredTool wrappers
- Async/sync compatibility for LangChain agents
- Example: `examples/langchain_example.py`

### OpenAI Function Calling
- **Direct usage** - no adapter needed!
- Our tool schemas are already OpenAI-compatible
- Example: `examples/openai_example.py`

## 🔄 Migration from Complex Structure

The legacy complex structure (10 tools, `tools/justifi/`) has been archived in `archive/`. This focused approach provides:
- ✅ Cleaner codebase
- ✅ Faster development
- ✅ Better testing
- ✅ Specialized payout expertise

## 🚢 Production Deployment

```bash
# Build production container
make prod-build

# Run production container
make prod-run

# Health check
make prod-health
```

## 🤝 Contributing

1. Focus on payout operations
2. Follow Python best practices
3. Add comprehensive tests
4. Use container development environment
5. Update documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file. 