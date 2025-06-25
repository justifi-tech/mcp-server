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

## 🏢 Production Deployment

### Single-Tenant Architecture

This MCP server follows a **single-tenant deployment model** where each customer runs their own isolated instance. This provides:

- ✅ **Maximum Security** - Your API credentials never leave your infrastructure
- ✅ **Complete Isolation** - No shared resources or data between customers
- ✅ **Full Control** - You manage your own deployment and updates
- ✅ **Zero Trust** - No external services have access to your credentials

### Deployment Options

#### Option 1: Local Development (Recommended)
```bash
# 1. Clone the repository
git clone <repository-url>
cd mcp-servers

# 2. Set up your credentials
cp env.example .env
# Edit .env with your JustiFi API credentials

# 3. Install and test
make install
make test
make mcp-test
```

#### Option 2: Docker Container (For AI Client Integration)
```bash
# 1. Create your environment file
cat > .env << EOF
JUSTIFI_CLIENT_ID=your_actual_client_id
JUSTIFI_CLIENT_SECRET=your_actual_client_secret
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
EOF

# 2. Build container (for AI client to execute)
docker build --target production -t justifi-mcp .

# 3. Configure your AI client to run the container
# (See Cursor configuration examples below)
```

#### Option 3: Kubernetes Deployment
```yaml
# justifi-mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: justifi-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: justifi-mcp
  template:
    metadata:
      labels:
        app: justifi-mcp
    spec:
      containers:
      - name: justifi-mcp
        image: justifi-mcp:latest
        env:
        - name: JUSTIFI_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: justifi-credentials
              key: client-id
        - name: JUSTIFI_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: justifi-credentials
              key: client-secret
```

### Security Best Practices

#### Credential Management
```bash
# Store credentials securely
chmod 600 .env

# Use environment-specific credentials
# Development: sandbox API keys
# Production: live API keys

# Never commit credentials to version control
echo ".env" >> .gitignore
```

#### Container Security
```bash
# Run as non-root user
docker run --user 1000:1000 --env-file .env justifi-mcp

# Use read-only filesystem
docker run --read-only --env-file .env justifi-mcp

# Limit resources
docker run --memory=256m --cpus=0.5 --env-file .env justifi-mcp
```

#### Network Security
- MCP uses stdio transport - no network ports exposed
- Server runs in isolated process
- No inbound network connections required
- All API calls go directly from your infrastructure to JustiFi

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

### Alternative: Container-based Configuration
```json
{
  "mcpServers": {
    "justifi": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", 
        "--env-file", "/path/to/your/.env",
        "justifi-mcp:latest"
      ]
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
# Start unified development environment
make dev-start

# Run tests (fast - no rebuilding needed)
make test

# Code quality checks
make lint format check-all

# Interactive development
make shell

# Stop development environment
make dev-stop
```

### Available Commands
```bash
make help           # Show all available commands
make dev-start      # Start development environment
make test           # Run unit tests in container
make lint           # Check code style
make format         # Auto-format code
make shell          # Interactive shell in dev container
make prod-build     # Build production container
make prod-run       # Run production container
make clean          # Clean all containers and volumes
```

### Project Structure
```
mcp-servers/
├── main.py                 # MCP server implementation
├── tools/
│   └── justifi/            # Modular JustiFi API integration
│       ├── __init__.py     # Tool exports
│       ├── core.py         # OAuth2 + HTTP client
│       ├── payments.py     # Payment tools
│       ├── payment_methods.py # Payment method tools
│       ├── payouts.py      # Payout tools
│       └── balances.py     # Balance transaction tools
├── tests/                  # Comprehensive test suite
│   ├── test_main.py        # MCP server tests
│   ├── test_justifi.py     # Core functionality tests
│   ├── test_payment_methods.py
│   ├── test_payouts.py
│   └── test_balances.py
├── docs/
│   ├── PRD-JustiFi-MCP-v1.1.md # Product requirements v1.1
│   ├── DEPLOYMENT.md       # Production deployment guide
│   └── endpoint-inventory.md # JustiFi API analysis
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Unified development environment
├── Dockerfile             # Production container
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