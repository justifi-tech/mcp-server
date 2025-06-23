# JustiFi MCP Server

A **Model Context Protocol (MCP)** server that provides AI assistants with secure access to the JustiFi payments platform. Built according to the official MCP specification for universal compatibility with Cursor, Claude Desktop, and other MCP clients.

## 🚀 What is MCP?

The **Model Context Protocol** is an open standard that enables AI applications to securely connect to external tools and data sources. Instead of building custom integrations for each AI client, MCP provides a standardized way for AI assistants to access your business tools.

**Key Benefits:**
- ✅ **Universal Compatibility** - Works with Cursor, Claude Desktop, and any MCP-compatible AI client
- ✅ **Standardized Communication** - Uses JSON-RPC 2.0 over stdio transport
- ✅ **Secure Architecture** - Proper capability negotiation and security boundaries
- ✅ **Future-Proof** - Built on open standards that scale across the AI ecosystem

## 🎯 Features

### JustiFi Payment Tools
- **Create Payment** - Process new payments with idempotency protection
- **Retrieve Payment** - Get payment details and status
- **List Payments** - Browse payments with pagination
- **Refund Payment** - Issue full or partial refunds

### Technical Features
- **OAuth2 Client-Credentials** authentication with token caching
- **Proper MCP Implementation** using the official Python SDK
- **Comprehensive Error Handling** with detailed error messages
- **Full Test Coverage** with mocked HTTP requests
- **Docker Support** for consistent development environments

## 📋 Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for databases)
- **JustiFi API Credentials** (Client ID & Secret)
- **MCP-compatible AI Client** (Cursor, Claude Desktop, etc.)

## 🛠 Quick Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd mcp-servers
cp env.example .env
# Edit .env with your JustiFi API credentials
make install
```

### 2. Configure Environment
```bash
# Required in .env file:
JUSTIFI_CLIENT_ID=your_justifi_client_id
JUSTIFI_CLIENT_SECRET=your_justifi_client_secret
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
```

### 3. Test the Server
```bash
# Test MCP server directly
make mcp-test

# Run unit tests
make test
```

## 🔗 Cursor Integration

### Configuration
Add this to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["/absolute/path/to/your/mcp-servers/main.py"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Usage Examples
Once configured, you can ask Cursor:

```
"Create a payment for $25.99 USD"
"Show me the details for payment pay_123"
"List the last 10 payments"
"Refund payment pay_123 for $10.00"
```

Cursor will automatically use the JustiFi tools to process these requests.

## 🏗 Development

### Development Workflow
```bash
# Start databases for development
make dev-start

# Run the MCP server locally
python main.py

# Stop development databases
make dev-stop
```

### Available Commands
```bash
make help           # Show all available commands
make install        # Install dependencies
make dev-start      # Start databases only
make start          # Start full stack with UIs
make test           # Run unit tests
make mcp-test       # Test MCP server directly
make clean          # Clean all containers and volumes
```

### Project Structure
```
mcp-servers/
├── main.py                 # MCP server implementation
├── tools/
│   ├── __init__.py
│   └── justifi.py          # JustiFi API integration
├── tests/
│   ├── test_main.py        # MCP server tests
│   └── test_justifi.py     # JustiFi tools tests
├── docker/
│   └── postgres/
│       └── init.sql        # Database initialization
├── docs/
│   └── PRD-JustiFi-MCP-v1.md  # Product requirements
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Full stack
├── docker-compose.dev.yml  # Development databases
└── Makefile               # Development commands
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_justifi.py -v

# Run with coverage
pytest tests/ --cov=tools --cov-report=html
```

### Manual Testing
```bash
# Test MCP server directly (stdio mode)
make mcp-test

# Test specific tool (example)
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_payments","arguments":{"limit":5}},"id":1}' | python main.py
```

## 🔒 Security

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique API credentials
- Rotate credentials regularly

### MCP Security
- Server runs in isolated process
- No network ports exposed
- Stdio transport provides secure communication
- Proper input validation and error handling

## 📚 Documentation

- **[MCP Specification](https://modelcontextprotocol.io/specification)** - Official protocol documentation
- **[JustiFi API Docs](https://docs.justifi.tech/)** - Payment platform documentation
- **[Product Requirements](docs/PRD-JustiFi-MCP-v1.md)** - Project requirements and roadmap

## 🐛 Troubleshooting

### Common Issues

**"Error: Missing required environment variables"**
```bash
# Solution: Set up your .env file
cp env.example .env
# Edit .env with your JustiFi credentials
```

**"JustiFi API connection failed"**
```bash
# Check your credentials
echo $JUSTIFI_CLIENT_ID
echo $JUSTIFI_CLIENT_SECRET
# Test API connectivity
make mcp-test
```

**"MCP server not connecting in Cursor"**
- Verify the absolute path in your MCP configuration
- Check that Python is available in your PATH
- Ensure environment variables are set correctly

### Debug Mode
```bash
# Run with verbose output
PYTHONPATH=/app python main.py

# Check logs
docker logs mcp-servers-postgres-1
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Documentation**: Check the [MCP specification](https://modelcontextprotocol.io/)
- **JustiFi Support**: Contact JustiFi support for API-related questions

---

**Built with ❤️ using the Model Context Protocol** 