# JustiFi MCP Server

A comprehensive **Model Context Protocol (MCP) server** for AI-assisted payment management. This server provides JustiFi payment tools across all major payment operations through the JustiFi API.

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

## 🚀 FastMCP Architecture

JustiFi MCP Server uses FastMCP for transport flexibility and reduced boilerplate.

### Transport Options

#### Stdio (Default - Local AI Clients)
```bash
python main.py
```

#### HTTP (Web-based AI Clients)
```bash
MCP_TRANSPORT=http MCP_PORT=3000 python main.py
```

#### Server-Sent Events
```bash
MCP_TRANSPORT=sse MCP_PORT=3000 python main.py
```

### Architecture

```
justifi-mcp-server/
├── modelcontextprotocol/    # FastMCP implementation
│   ├── server.py           # FastMCP server setup  
│   └── config.py           # Transport configuration
├── python/                 # Core tools and utilities
│   ├── core.py            # JustiFi API client
│   ├── tools/             # Tool implementations
│   └── adapters/          # Framework adapters
└── main.py                # FastMCP entry point
```

### Multi-Framework Support

The server provides multi-framework support:

```python
# LangChain
from python.adapters.langchain import JustiFiLangChainAdapter

# OpenAI
from python.tools.payments import retrieve_payment
```

## 🎯 Comprehensive Payment Management

This MCP server provides complete payment management capabilities across multiple domains:

### Payment Tools
- `retrieve_payment` - Get detailed payment information
- `list_payments` - List payments with pagination

### Payout Tools
- `retrieve_payout` - Get detailed payout information
- `list_payouts` - List payouts with pagination  
- `get_payout_status` - Quick status check for payouts
- `get_recent_payouts` - Get the most recent payouts

### Refund Tools
- `retrieve_refund` - Get refund details by ID
- `list_refunds` - List all refunds with pagination
- `list_payment_refunds` - List refunds for a specific payment

### Balance Transaction Tools
- `list_balance_transactions` - List fund movements with filtering
- `retrieve_balance_transaction` - Get specific balance transaction

### Dispute Tools
- `list_disputes` - List disputes with pagination
- `retrieve_dispute` - Get dispute details by ID

### Checkout Tools
- `list_checkouts` - List checkouts with filtering
- `retrieve_checkout` - Get checkout details by ID

### Payment Method Tools
- `retrieve_payment_method` - Get payment method by token



## 🚀 Quick Start

### Option 1: NPX (Recommended for Easy Installation)

**Prerequisites**: Node.js 16+ and Python 3.11+

```bash
# Run directly with NPX - automatically handles Python dependencies
npx @justifi/mcp-server

# Set your JustiFi credentials first
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"

# Run health check to verify setup
npx @justifi/mcp-server --health-check
```

**Key benefits of NPX approach:**
- ✅ **Automatic setup** - Handles Python dependencies and virtual environments
- ✅ **Safe by default** - Uses virtual environments to avoid global package conflicts
- ✅ **Cross-platform** - Works on Windows, macOS, and Linux
- ✅ **No manual installation** - Everything handled automatically

### Option 2: Local Development Setup

**Prerequisites**: Python 3.11+, Docker (optional)

1. **Clone and configure**:
   ```bash
   git clone <repository>
   cd mcp-servers
   cp env.example .env
   # Edit .env with your JustiFi API credentials
   ```

2. **Install dependencies** (optional for local development):
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Test the setup**:
   ```bash
   make test
   ```

## 🔧 Development Commands

All development uses Docker containers for consistency:

```bash
# Start MCP server with auto-restart
make dev

# Run all tests
make test

# Interactive development shell
make shell

# View logs
make logs

### Code Quality

The project uses **ruff** for fast, comprehensive linting and formatting:

```bash
# Run linting checks
make lint

# Auto-format code
make format

# Run all quality checks (lint + format + test)
make check-all
```

**Note**: MyPy type checking has been intentionally excluded from the standard workflow to focus on runtime correctness and maintainability. The core business logic is thoroughly tested with 74/74 tests passing.

# Clean up containers
make clean
```

## 🧪 Testing

### All Tests
```bash
# Run all tests
make test
```

### Individual Test Files
```bash
# Run specific test files
docker-compose run --rm dev pytest tests/test_payout_tools.py -v
docker-compose run --rm dev pytest tests/test_payment_tools.py -v
docker-compose run --rm dev pytest tests/test_main.py -v
```

## 🔌 MCP Integration

### Cursor IDE

#### Method 1: NPX (Recommended)
Add to your `cursor_mcp_config.json`:
```json
{
  "mcpServers": {
    "justifi": {
      "command": "npx",
      "args": ["@justifi/mcp-server"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret",
        "JUSTIFI_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

#### Method 2: Local Development
Add to your `cursor_mcp_config.json`:
```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/mcp-servers",
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Claude Desktop

Claude Desktop supports MCP servers through its configuration file. Choose one of these methods:

#### Method 1: NPX (Recommended)
Configure Claude Desktop by editing your config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`  
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "justifi": {
      "command": "npx",
      "args": ["@justifi/mcp-server"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret",
        "JUSTIFI_ENVIRONMENT": "sandbox"
      }
    }
  }
}
```

#### Method 2: Direct Python Execution (Local Development)
1. **Start the server** in stdio mode:
   ```bash
   cd /path/to/mcp-servers
   python main.py
   ```

2. **Configure Claude Desktop** with direct Python execution:
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

#### Method 3: HTTP Mode with mcp-remote
1. **Start the server** in HTTP mode:
   ```bash
   cd /path/to/mcp-servers
   MCP_TRANSPORT=http MCP_PORT=3000 python main.py
   ```

2. **Configure Claude Desktop** to use mcp-remote:
   ```json
   {
     "mcpServers": {
       "justifi": {
         "command": "npx",
         "args": [
           "-y",
           "mcp-remote",
           "http://localhost:3000/mcp"
         ]
       }
     }
   }
   ```

3. **Set environment variables** in your shell before starting the server:
   ```bash
   export JUSTIFI_CLIENT_ID="your_client_id"
   export JUSTIFI_CLIENT_SECRET="your_client_secret"
   export JUSTIFI_ENABLED_TOOLS="all"
   ```

#### Verification
After configuration, restart Claude Desktop and you should see JustiFi payment tools available in your conversations. You can test with prompts like:
- "List recent payouts"
- "Get the status of payout po_ABC123"
- "Show me payment details for py_XYZ789"

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
```

**Note**: No AI model API keys needed! Those are handled by MCP clients, not this server.

## 🔄 API Drift Monitoring

Monitor JustiFi API changes automatically:
```bash
# Check for API changes
make drift-check
```

**Automation**: GitHub Actions workflow runs weekly to detect API changes and create PRs/issues automatically.

## 🏛️ Architecture

### Clean & Comprehensive
- **Full payment management**: Tools across all payment domains
- **Multi-framework support**: MCP (primary), LangChain, OpenAI examples
- **Container-first development**: Docker for consistency
- **Focused testing**: Critical error scenarios only

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

- [API Endpoint Inventory](docs/endpoint-inventory.md) - Verified JustiFi API endpoints
- [API Drift Monitoring](docs/API-DRIFT-MONITORING.md) - Automated API change detection

## 🔌 Framework Integration

### MCP (Model Context Protocol)
- **Primary integration** for IDE usage (Cursor, VS Code, Windsurf)
- Full MCP server with tool schemas and JSON-RPC 2.0 protocol
- See [MCP Integration](#-mcp-integration) section above

### LangChain
- **Dedicated adapter** with StructuredTool wrappers
- Async/sync compatibility for LangChain agents
- Examples: [`examples/langchain/`](./examples/langchain/)

### OpenAI Function Calling
- **Direct usage** - no adapter needed!
- Our tool schemas are already OpenAI-compatible
- Examples: [`examples/openai/`](./examples/openai/)

## 🤝 Contributing

1. Focus on comprehensive payment management
2. Follow Python best practices
3. Add tests for critical error scenarios only
4. Use container development environment
5. Update documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file. 