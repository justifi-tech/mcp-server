# JustiFi MCP Server

A simple NPX wrapper for the JustiFi MCP Server that enables AI assistants to process payments, manage payment methods, and handle payouts through the JustiFi API.

## Quick Start

```bash
# Run directly with npx (recommended)
npx @justifi/mcp-server

# Or install globally
npm install -g @justifi/mcp-server
justifi-mcp-server
```

## Prerequisites

1. **Python 3.11+** - The server runs on Python
2. **Python Dependencies** - Install required packages:
   ```bash
   pip install mcp fastmcp httpx pydantic python-dotenv langsmith starlette uvicorn
   ```

3. **JustiFi API Credentials** - Get from [JustiFi Dashboard](https://dashboard.justifi.ai)

## Environment Variables

```bash
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"
export JUSTIFI_ENVIRONMENT="sandbox"  # or "production"
```

## Claude Desktop Integration

Add to `~/.config/claude_desktop/claude_desktop_config.json`:

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

## Available Tools

- **Payments**: Create, retrieve, list, refund payments
- **Payment Methods**: Create and retrieve tokenized payment methods  
- **Payouts**: Retrieve and list payout information
- **Balance Transactions**: List account balance movements
- **Checkouts**: Create and manage checkout sessions
- **Disputes**: Handle payment disputes and chargebacks
- **Refunds**: Process and track refunds

## Help

```bash
npx @justifi/mcp-server --help
npx @justifi/mcp-server --version
```

## Repository

Full source code: [github.com/justifi-tech/mcp-server](https://github.com/justifi-tech/mcp-server) 