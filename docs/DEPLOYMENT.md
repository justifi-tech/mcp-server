# JustiFi MCP Server - Production Deployment Guide

This guide covers deploying the JustiFi MCP server in production environments using standalone Docker containers (no docker-compose required).

## 🏗️ Production Architecture

The production setup uses:
- **Standalone Docker container** for the MCP server
- **Environment variables** for configuration
- **Non-root user** for security
- **Health checks** for monitoring
- **Restart policies** for reliability

## 📋 Prerequisites

1. **Docker** installed on your production server
2. **JustiFi API credentials** (Client ID and Secret)
3. **Environment file** with production settings

## 🚀 Quick Deployment

### 1. Prepare Environment

Create a production `.env` file:

```bash
# Required JustiFi API credentials
JUSTIFI_CLIENT_ID=your_production_client_id
JUSTIFI_CLIENT_SECRET=your_production_client_secret

# Optional configuration
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_key  # Optional for observability
```

### 2. Build Production Container

```bash
# Build the production image
make prod-build

# Or manually:
docker build --target production -t justifi-mcp:latest .
```

### 3. Deploy Options

#### Option A: Interactive Mode (for testing)
```bash
# Run interactively (good for testing)
make prod-run

# Or manually:
docker run -it --name justifi-mcp-server \
  --env-file .env \
  --rm \
  justifi-mcp:latest
```

#### Option B: Background Service (recommended)
```bash
# Start as background service
make prod-start

# Or manually:
docker run -d --name justifi-mcp-server \
  --env-file .env \
  --restart unless-stopped \
  justifi-mcp:latest
```

## 🔧 Production Management

### Health Monitoring
```bash
# Check container health
make prod-health

# Manual health check
docker exec justifi-mcp-server python main.py --health
```

### Log Management
```bash
# View logs
make prod-logs

# Follow logs in real-time
docker logs justifi-mcp-server -f

# View last 100 lines
docker logs justifi-mcp-server --tail=100
```

### Container Management
```bash
# Stop the service
make prod-stop

# Restart the service
make prod-stop && make prod-start

# Clean up everything
make prod-clean
```

## 🔒 Security Best Practices

### Container Security
- ✅ **Non-root user**: Container runs as `mcpuser`
- ✅ **Minimal image**: Production stage only includes necessary files
- ✅ **No secrets in image**: Environment variables provided at runtime
- ✅ **Read-only filesystem**: Consider adding `--read-only` flag

### Enhanced Security Deployment
```bash
docker run -d --name justifi-mcp-server \
  --env-file .env \
  --restart unless-stopped \
  --read-only \
  --tmpfs /tmp \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  justifi-mcp:latest
```

### Network Security
```bash
# Create isolated network
docker network create --driver bridge justifi-network

# Run with custom network
docker run -d --name justifi-mcp-server \
  --network justifi-network \
  --env-file .env \
  --restart unless-stopped \
  justifi-mcp:latest
```

## 📊 Monitoring & Observability

### Health Check Endpoint
The container includes a built-in health check:
```bash
# Returns JSON with health status
docker exec justifi-mcp-server python main.py --health
```

Example healthy response:
```json
{
  "status": "healthy",
  "timestamp": 1735135200.0,
  "environment": "configured",
  "justifi_api": "connected"
}
```

### LangSmith Tracing (Optional)
Enable observability with LangSmith:
```bash
# Add to .env file
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

### Log Aggregation
For production monitoring, consider:
- **Fluentd/Fluent Bit** for log collection
- **Prometheus** for metrics
- **Grafana** for dashboards

Example with log driver:
```bash
docker run -d --name justifi-mcp-server \
  --env-file .env \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  justifi-mcp:latest
```

## 🔄 Updates & Rollbacks

### Update Process
```bash
# 1. Build new image
make prod-build

# 2. Stop current container
make prod-stop

# 3. Start new container
make prod-start

# 4. Verify health
make prod-health
```

### Blue-Green Deployment
```bash
# Start new version alongside old
docker run -d --name justifi-mcp-server-new \
  --env-file .env \
  justifi-mcp:latest

# Test new version
docker exec justifi-mcp-server-new python main.py --health

# Switch traffic (stop old, rename new)
docker stop justifi-mcp-server
docker rm justifi-mcp-server
docker rename justifi-mcp-server-new justifi-mcp-server
```

## 🐛 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs for errors
docker logs justifi-mcp-server

# Common causes:
# - Missing environment variables
# - Invalid JustiFi credentials
# - Port conflicts
```

#### Health Check Fails
```bash
# Run health check manually
docker exec justifi-mcp-server python main.py --health

# Check environment variables
docker exec justifi-mcp-server env | grep JUSTIFI
```

#### Permission Issues
```bash
# Verify container runs as non-root
docker exec justifi-mcp-server whoami
# Should return: mcpuser
```

### Debug Mode
```bash
# Run with debug output
docker run -it --name justifi-mcp-debug \
  --env-file .env \
  --rm \
  justifi-mcp:latest bash

# Then inside container:
python main.py --health
python main.py  # Run MCP server
```

## 🌐 Integration with IDEs

### Cursor Configuration
Configure Cursor to connect to the containerized MCP server:

```json
{
  "mcpServers": {
    "justifi": {
      "command": "docker",
      "args": [
        "exec", "-i", "justifi-mcp-server",
        "python", "main.py"
      ]
    }
  }
}
```

### VS Code Configuration
Similar setup for VS Code MCP extensions.

## 📈 Scaling Considerations

### Horizontal Scaling
```bash
# Run multiple instances with different names
docker run -d --name justifi-mcp-server-1 \
  --env-file .env justifi-mcp:latest

docker run -d --name justifi-mcp-server-2 \
  --env-file .env justifi-mcp:latest
```

### Resource Limits
```bash
# Set memory and CPU limits
docker run -d --name justifi-mcp-server \
  --env-file .env \
  --memory=512m \
  --cpus=0.5 \
  --restart unless-stopped \
  justifi-mcp:latest
```

## 🔧 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JUSTIFI_CLIENT_ID` | ✅ | - | JustiFi API Client ID |
| `JUSTIFI_CLIENT_SECRET` | ✅ | - | JustiFi API Client Secret |
| `JUSTIFI_BASE_URL` | ❌ | `https://api.justifi.ai/v1` | JustiFi API Base URL |
| `LANGCHAIN_TRACING_V2` | ❌ | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | ❌ | - | LangSmith API key |

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review container logs: `make prod-logs`
3. Verify environment configuration
4. Test with interactive mode: `make prod-run` 