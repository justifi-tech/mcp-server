# @justifi/mcp-server

> **JustiFi MCP Server** - NPX wrapper for seamless AI-assisted payment management

[![NPM Version](https://img.shields.io/npm/v/@justifi/mcp-server)](https://www.npmjs.com/package/@justifi/mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

The fastest way to get started with JustiFi MCP Server:

```bash
# Run directly with npx (no installation required)
npx @justifi/mcp-server

# Or install globally
npm install -g @justifi/mcp-server
justifi-mcp-server
```

## 📋 Prerequisites

- **Node.js 18+** (for NPX wrapper)
- **Python 3.11+** (automatically managed)
- **JustiFi API Credentials**:
  - `JUSTIFI_CLIENT_ID`
  - `JUSTIFI_CLIENT_SECRET`
  - `JUSTIFI_BASE_URL` (optional, defaults to https://api.justifi.ai)

## 🛠️ What This Package Does

This NPM package is a **smart wrapper** that:

1. **Auto-installs Python dependencies** using `uv` (fastest Python package manager)
2. **Manages the Python MCP server** process automatically
3. **Provides health checks** and error recovery
4. **Simplifies deployment** for AI assistants and IDEs

## 🎯 AI Assistant Integration

### Claude Desktop

Add to your `~/.claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "justifi": {
      "command": "npx",
      "args": ["@justifi/mcp-server"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Cursor IDE

Add to your MCP settings:

```json
{
  "mcpServers": {
    "justifi": {
      "command": "npx @justifi/mcp-server",
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

## 🔧 Advanced Usage

### Health Check

```bash
npx @justifi/mcp-server --health-check
```

### Custom Python Path

```bash
PYTHON_PATH=/usr/bin/python3.11 npx @justifi/mcp-server
```

### Debug Mode

```bash
DEBUG=1 npx @justifi/mcp-server
```

## 🧰 Available Tools

The MCP server provides **10 comprehensive payment tools**:

### Payment Management (5 tools)
- `create_payment` - Process new payments with idempotency
- `retrieve_payment` - Get payment details by ID  
- `list_payments` - Search and filter payments
- `refund_payment` - Issue full or partial refunds
- `list_refunds` - Track refund history

### Payment Methods (2 tools)
- `create_payment_method` - Tokenize payment cards
- `retrieve_payment_method` - Get tokenized payment data

### Payouts (2 tools)
- `retrieve_payout` - Get payout details
- `list_payouts` - Track settlement history

### Balance Tracking (1 tool)
- `list_balance_transactions` - Monitor fund movements

## 🔐 Security & Authentication

- **OAuth2 Client-Credentials** flow with automatic token refresh
- **Environment-based** credential management
- **No sensitive data logging** or storage
- **Automatic 401 retry** with token refresh

## 🐛 Troubleshooting

### Common Issues

1. **"Python not found"**
   ```bash
   # Install Python 3.11+ or set custom path
   PYTHON_PATH=/usr/bin/python3 npx @justifi/mcp-server
   ```

2. **"uv not found"**
   ```bash
   # The wrapper will auto-install uv, but you can install manually:
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **"Authentication failed"**
   ```bash
   # Verify your JustiFi credentials
   echo $JUSTIFI_CLIENT_ID
   echo $JUSTIFI_CLIENT_SECRET
   ```

4. **"Connection refused"**
   ```bash
   # Run health check
   npx @justifi/mcp-server --health-check
   ```

### Debug Logs

Enable detailed logging:

```bash
DEBUG=1 LANGCHAIN_TRACING_V2=true npx @justifi/mcp-server
```

## 📚 Documentation

- **Full Documentation**: [GitHub Repository](https://github.com/justifi-tech/mcp-server)
- **JustiFi API Docs**: [https://docs.justifi.ai](https://docs.justifi.ai)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/justifi-tech/mcp-server/issues)
- **Documentation**: [GitHub Repository](https://github.com/justifi-tech/mcp-server)
- **JustiFi Support**: [https://justifi.ai/contact](https://justifi.ai/contact)

## 📄 License

MIT License - see [LICENSE](https://github.com/justifi-tech/mcp-server/blob/main/LICENSE) for details.

---

**Made with ❤️ by the JustiFi team** 