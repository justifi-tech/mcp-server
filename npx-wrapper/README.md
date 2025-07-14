# JustiFi MCP Server - NPX Wrapper

[![npm version](https://badge.fury.io/js/@justifi%2Fmcp-server.svg)](https://badge.fury.io/js/@justifi%2Fmcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Easy-to-use NPX wrapper for the JustiFi MCP (Model Context Protocol) Server. This wrapper allows you to run the JustiFi MCP server with a simple `npx` command, automatically handling Python dependencies and environment setup.

## Quick Start

```bash
# Run directly with NPX (recommended)
npx @justifi/mcp-server

# Or install globally
npm install -g @justifi/mcp-server
justifi-mcp-server
```

## Prerequisites

- **Node.js**: 16.0.0 or later
- **Python**: 3.11 or later
- **JustiFi API Credentials**: Client ID and Client Secret

## Installation

The NPX wrapper automatically handles Python dependency installation. On first run, it will:

1. Detect your Python installation
2. Create a virtual environment (if needed)
3. Install required Python packages
4. Verify the installation

### Manual Installation

If you prefer to install the package locally:

```bash
npm install @justifi/mcp-server
```

## Usage

### Basic Usage

```bash
# Run with default settings (stdio transport)
npx @justifi/mcp-server

# Run health check
npx @justifi/mcp-server --health-check

# Show help
npx @justifi/mcp-server --help

# Show version information
npx @justifi/mcp-server --version
```

### Environment Variables

Configure the server using environment variables:

```bash
# Required: JustiFi API credentials
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"

# Optional: API environment (default: sandbox)
export JUSTIFI_ENVIRONMENT="sandbox"  # or "production"

# Optional: Transport configuration
export MCP_TRANSPORT="stdio"    # stdio, http, or sse
export MCP_HOST="localhost"     # for http/sse transport
export MCP_PORT="3000"          # for http/sse transport

# Optional: Logging
export LOG_LEVEL="INFO"         # DEBUG, INFO, WARNING, ERROR
```

### Transport Modes

The server supports three transport modes:

#### 1. STDIO (Default)
Perfect for local AI clients like Claude Desktop:
```bash
npx @justifi/mcp-server
```

#### 2. HTTP Server
For web-based integrations:
```bash
MCP_TRANSPORT=http MCP_PORT=3000 npx @justifi/mcp-server
```

#### 3. Server-Sent Events (SSE)
For real-time web applications:
```bash
MCP_TRANSPORT=sse MCP_PORT=3000 npx @justifi/mcp-server
```

## Configuration for AI Clients

### Claude Desktop

Add to your `~/.config/claude_desktop/claude_desktop_config.json`:

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

### Cursor IDE

Add to your Cursor MCP configuration:

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

### Other MCP Clients

For any MCP-compatible client, use:
- **Command**: `npx`
- **Args**: `["@justifi/mcp-server"]`
- **Environment**: Set your JustiFi credentials

## Available Tools

The JustiFi MCP server provides AI assistants with access to:

- **Payments**: Create, retrieve, update, and cancel payments
- **Refunds**: Process full and partial refunds
- **Payouts**: Manage seller payouts and disbursements
- **Disputes**: Handle payment disputes and chargebacks
- **Balances**: Check account and available balances
- **Checkouts**: Create and manage payment checkouts
- **Payment Methods**: Manage stored payment methods

## Troubleshooting

### Common Issues

#### Python Not Found
```bash
# Error: Python not found
# Solution: Install Python 3.11+ and ensure it's in PATH
python3 --version  # Should show 3.11+
```

#### Permission Errors
```bash
# Error: Permission denied during installation
# Solution: Check write permissions or use --unsafe-perm
npm install -g @justifi/mcp-server --unsafe-perm
```

#### Virtual Environment Issues
```bash
# Skip virtual environment creation
export JUSTIFI_MCP_NO_VENV=true
npx @justifi/mcp-server
```

#### Installation Problems
```bash
# Skip automatic installation
export JUSTIFI_MCP_SKIP_INSTALL=true
npx @justifi/mcp-server

# Manual dependency installation
cd ~/.npm/_npx/*/node_modules/@justifi/mcp-server
python3 -m pip install -e .
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
npx @justifi/mcp-server
```

### Health Check

Verify everything is working:

```bash
npx @justifi/mcp-server --health-check
```

Expected output:
```
✅ JustiFi FastMCP server healthy
📊 Details: {"status":"healthy","fastmcp_server":"created","justifi_api":"connected","token_acquired":true}
```

### Platform-Specific Notes

#### Windows
- Uses `py` command if available
- Handles Windows path separators
- Supports PowerShell and Command Prompt

#### macOS
- Uses `python3` by default
- Handles system Python vs. Homebrew Python
- Supports both Intel and Apple Silicon

#### Linux
- Uses system Python or virtual environments
- Handles various distributions
- Supports containerized environments

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JUSTIFI_CLIENT_ID` | JustiFi API Client ID | - | ✅ |
| `JUSTIFI_CLIENT_SECRET` | JustiFi API Client Secret | - | ✅ |
| `JUSTIFI_ENVIRONMENT` | API Environment | `sandbox` | ❌ |
| `MCP_TRANSPORT` | Transport protocol | `stdio` | ❌ |
| `MCP_HOST` | Server host (HTTP/SSE) | `localhost` | ❌ |
| `MCP_PORT` | Server port (HTTP/SSE) | `3000` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `JUSTIFI_MCP_NO_VENV` | Skip virtual environment | `false` | ❌ |
| `JUSTIFI_MCP_SKIP_INSTALL` | Skip auto-install | `false` | ❌ |

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/justifi-tech/mcp-servers.git
cd mcp-servers

# Install dependencies
npm install

# Run in development mode
npm run dev
```

### Testing

```bash
# Run tests
npm test

# Run health check
npm run test
```

## Support

- **Documentation**: [https://docs.justifi.ai/mcp](https://docs.justifi.ai/mcp)
- **Issues**: [GitHub Issues](https://github.com/justifi-tech/mcp-servers/issues)
- **Email**: support@justifi.ai

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Changelog

### v1.0.0
- Initial release
- NPX wrapper for Python MCP server
- Cross-platform support
- Automatic dependency management
- Health check functionality
- Support for all MCP transport modes