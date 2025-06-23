# JustiFi MCP Server - Customer Setup Guide

Welcome! This guide will help you deploy your own secure instance of the JustiFi MCP server that integrates with Cursor and other AI development tools.

## 🔒 Why Single-Tenant?

Your JustiFi MCP server runs exclusively on **your infrastructure** with **your credentials**. This means:

- ✅ **Your API keys never leave your environment**
- ✅ **Complete data isolation** from other customers
- ✅ **Full control** over updates and configuration
- ✅ **Compliance-ready** for financial data handling

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] **JustiFi Account** with API access
- [ ] **JustiFi API Credentials** (Client ID & Secret)
- [ ] **Python 3.11+** installed
- [ ] **Git** for cloning the repository
- [ ] **Cursor IDE** or another MCP-compatible AI client

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your JustiFi Credentials

1. Log into your JustiFi dashboard
2. Navigate to **Settings** → **API Keys**
3. Create or copy your:
   - **Client ID** (starts with `client_`)
   - **Client Secret** (starts with `secret_`)

### Step 2: Deploy Your MCP Server

```bash
# 1. Clone the repository
git clone https://github.com/your-org/justifi-mcp-server.git
cd justifi-mcp-server

# 2. Set up your environment
cp env.example .env

# 3. Edit .env with your credentials
# Use your favorite editor (nano, vim, VS Code, etc.)
nano .env
```

Add your JustiFi credentials to the `.env` file:
```env
JUSTIFI_CLIENT_ID=your_actual_client_id_here
JUSTIFI_CLIENT_SECRET=your_actual_client_secret_here
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
```

### Step 3: Test Your Setup

```bash
# Install dependencies and test
make install
make test
make mcp-test
```

You should see:
```
✅ JustiFi API connection successful
✅ All tests passed
```

### Step 4: Configure Cursor

Add this to your Cursor MCP configuration file:

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.cursor-small/mcp_servers.json`

**Windows**: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.cursor-small\mcp_servers.json`

**Linux**: `~/.config/Cursor/User/globalStorage/rooveterinaryinc.cursor-small\mcp_servers.json`

```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["/absolute/path/to/your/justifi-mcp-server/main.py"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/your/justifi-mcp-server/` with the actual path where you cloned the repository.

### Step 5: Test in Cursor

1. Restart Cursor
2. Open any project
3. Try asking: *"Create a test payment for $10.99"*
4. Cursor should now have access to JustiFi payment tools!

## 🐳 Production Deployment (Docker)

For production environments, use Docker for better isolation and security:

### Option 1: Simple Docker

```bash
# Build production container
make prod-build

# Start production server
make prod-start

# Check health
make prod-health

# View logs
make prod-logs
```

### Option 2: Custom Docker Setup

```bash
# Create secure environment file
cat > .env << EOF
JUSTIFI_CLIENT_ID=your_production_client_id
JUSTIFI_CLIENT_SECRET=your_production_client_secret
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
EOF

# Secure the file
chmod 600 .env

# Build and run
docker build --target production -t justifi-mcp .
docker run --rm -i --env-file .env justifi-mcp
```

### Cursor Configuration for Docker

```json
{
  "mcpServers": {
    "justifi": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", 
        "--env-file", "/path/to/your/.env",
        "justifi-mcp"
      ]
    }
  }
}
```

## 🔧 Available Tools

Once configured, you'll have access to these JustiFi tools in Cursor:

### 💳 Create Payment
```
"Create a payment for $25.99 USD with idempotency key 'order-123'"
```

### 🔍 Retrieve Payment
```
"Get details for payment pay_abc123"
```

### 📋 List Payments
```
"Show me the last 10 payments"
"List payments with pagination after cursor xyz"
```

### 💰 Refund Payment
```
"Refund payment pay_abc123 for $10.00"
"Issue a full refund for payment pay_abc123"
```

## 🛡️ Security Best Practices

### Environment Security
```bash
# Secure your environment file
chmod 600 .env
chown $(whoami):$(whoami) .env

# Never commit credentials
echo ".env" >> .gitignore
```

### API Key Management
- **Development**: Use JustiFi sandbox credentials
- **Production**: Use live JustiFi credentials
- **Rotation**: Update credentials regularly
- **Monitoring**: Monitor API usage in JustiFi dashboard

### Container Security
```bash
# Run with limited privileges
docker run --user 1000:1000 --read-only --env-file .env justifi-mcp

# Use resource limits
docker run --memory=256m --cpus=0.5 --env-file .env justifi-mcp
```

## 🔧 Troubleshooting

### Common Issues

**❌ "Missing environment variables"**
```bash
# Check your .env file exists and has correct values
cat .env
# Should show your JUSTIFI_CLIENT_ID and JUSTIFI_CLIENT_SECRET
```

**❌ "JustiFi API connection failed"**
```bash
# Test your credentials manually
curl -X POST https://api.justifi.ai/v1/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET"
```

**❌ "Cursor can't connect to MCP server"**
- Verify the absolute path in your MCP configuration
- Check that Python is in your PATH: `which python`
- Restart Cursor after configuration changes

**❌ "Permission denied"**
```bash
# Make sure main.py is executable
chmod +x main.py

# Check file ownership
ls -la main.py
```

### Debug Mode

```bash
# Run with verbose output
python main.py --health

# Test individual components
python -c "
import asyncio
from tools.justifi import list_payments
result = asyncio.run(list_payments(limit=1))
print(result)
"
```

### Getting Help

- **Technical Issues**: Check the troubleshooting section above
- **JustiFi API Questions**: Contact JustiFi support
- **MCP Configuration**: Check [MCP documentation](https://modelcontextprotocol.io/)

## 📊 Monitoring Your Instance

### Health Checks
```bash
# Check server health
python main.py --health

# Monitor in production
docker exec justifi-mcp-server python main.py --health
```

### Log Monitoring
```bash
# View recent logs
make prod-logs

# Or directly with Docker
docker logs justifi-mcp-server --tail=100
```

### API Usage Monitoring
- Monitor your API usage in the JustiFi dashboard
- Set up alerts for unusual activity
- Review payment logs regularly

## 🔄 Updates and Maintenance

### Updating Your Instance
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
make prod-stop
make prod-start
```

### Backup and Recovery
```bash
# Backup your configuration
cp .env .env.backup

# Document your Cursor configuration
# Keep a copy of your MCP server settings
```

## 📞 Support

- **Setup Issues**: Check this guide and troubleshooting section
- **JustiFi API**: Contact JustiFi support team
- **Feature Requests**: Open a GitHub issue
- **Security Concerns**: Contact our security team

---

## ✅ Setup Checklist

- [ ] JustiFi credentials obtained
- [ ] Repository cloned and configured
- [ ] Environment variables set in `.env`
- [ ] Dependencies installed (`make install`)
- [ ] Tests passing (`make test`)
- [ ] MCP server responding (`make mcp-test`)
- [ ] Cursor configured with absolute path
- [ ] Test payment created successfully
- [ ] Security best practices implemented

**Congratulations!** 🎉 You now have your own secure JustiFi MCP server running on your infrastructure.

Your API credentials never leave your environment, and you have full control over your payment processing integration with AI development tools. 