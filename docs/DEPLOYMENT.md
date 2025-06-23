# JustiFi MCP Server - Deployment Guide

This guide provides detailed instructions for deploying the JustiFi MCP server in various environments using the single-tenant architecture model.

## 🏗️ Architecture Overview

### Single-Tenant Model
Each customer runs their own isolated instance of the MCP server with their own JustiFi API credentials. This ensures:

- **Security Isolation**: Credentials never leave customer infrastructure
- **Compliance**: Meets strict security requirements for financial data
- **Customization**: Each customer can modify their instance as needed
- **Reliability**: No shared infrastructure points of failure

### Communication Flow
```
AI Client (Cursor) ←→ MCP Server (Your Infrastructure) ←→ JustiFi API
```

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Git
- JustiFi API credentials (sandbox for development)

### Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd mcp-servers

# 2. Create environment file
cp env.example .env

# 3. Edit .env with your credentials
JUSTIFI_CLIENT_ID=your_sandbox_client_id
JUSTIFI_CLIENT_SECRET=your_sandbox_client_secret
JUSTIFI_BASE_URL=https://api.justifi.ai/v1

# 4. Install and test
make install
make test
make mcp-test
```

### Cursor Configuration
```json
{
  "mcpServers": {
    "justifi": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-servers/main.py"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_sandbox_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_sandbox_client_secret"
      }
    }
  }
}
```

## 🐳 Docker Deployment

### Option 1: Simple Container
```bash
# Build image
docker build -t justifi-mcp .

# Create environment file
cat > .env << EOF
JUSTIFI_CLIENT_ID=your_client_id
JUSTIFI_CLIENT_SECRET=your_client_secret
JUSTIFI_BASE_URL=https://api.justifi.ai/v1
EOF

# Run container
docker run --rm -i --env-file .env justifi-mcp
```

### Option 2: Docker Compose (Recommended)
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  justifi-mcp:
    build: .
    env_file: .env
    stdin_open: true
    tty: true
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
```

```bash
# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Configure Cursor to connect to container
```

### Cursor Configuration for Docker
```json
{
  "mcpServers": {
    "justifi": {
      "command": "docker",
      "args": [
        "exec", "-i", "mcp-servers-justifi-mcp-1", 
        "python", "main.py"
      ]
    }
  }
}
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Container registry access

### Step 1: Build and Push Image
```bash
# Build image
docker build -t your-registry/justifi-mcp:v1.0.0 .

# Push to registry
docker push your-registry/justifi-mcp:v1.0.0
```

### Step 2: Create Secret
```bash
# Create credentials secret
kubectl create secret generic justifi-credentials \
  --from-literal=client-id=your_client_id \
  --from-literal=client-secret=your_client_secret \
  --from-literal=base-url=https://api.justifi.ai/v1
```

### Step 3: Deploy Application
```yaml
# justifi-mcp.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: justifi-mcp
  labels:
    app: justifi-mcp
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
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: justifi-mcp
        image: your-registry/justifi-mcp:v1.0.0
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
        - name: JUSTIFI_BASE_URL
          valueFrom:
            secretKeyRef:
              name: justifi-credentials
              key: base-url
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        stdin: true
        tty: true
---
apiVersion: v1
kind: Service
metadata:
  name: justifi-mcp-service
spec:
  selector:
    app: justifi-mcp
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

```bash
# Deploy
kubectl apply -f justifi-mcp.yaml

# Verify deployment
kubectl get pods -l app=justifi-mcp
kubectl logs -l app=justifi-mcp
```

### Cursor Configuration for Kubernetes
```json
{
  "mcpServers": {
    "justifi": {
      "command": "kubectl",
      "args": [
        "exec", "-i", 
        "deployment/justifi-mcp", 
        "--", "python", "main.py"
      ]
    }
  }
}
```

## 🔒 Security Hardening

### Environment Security
```bash
# Secure environment file
chmod 600 .env
chown root:root .env

# Use secrets management
# AWS: AWS Secrets Manager
# Azure: Azure Key Vault
# GCP: Secret Manager
# HashiCorp: Vault
```

### Container Security
```dockerfile
# Multi-stage build for smaller attack surface
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --chown=mcpuser:mcpuser . .
USER mcpuser
CMD ["python", "main.py"]
```

### Network Security
```bash
# Use private container networks
docker network create --driver bridge justifi-network

# Run with network isolation
docker run --network justifi-network --env-file .env justifi-mcp
```

## 📊 Monitoring & Observability

### Health Checks
```python
# Add to main.py for health monitoring
import asyncio
import json
import sys

async def health_check():
    """Simple health check for monitoring"""
    try:
        # Test environment variables
        from tools.justifi import JustiFiClient
        client = JustiFiClient()
        
        # Test API connectivity (without making actual calls)
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "environment": "configured"
        }
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Add health check endpoint for monitoring
if len(sys.argv) > 1 and sys.argv[1] == "--health":
    result = asyncio.run(health_check())
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "healthy" else 1)
```

### Logging Configuration
```python
import logging
import os

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/justifi-mcp.log') if os.path.exists('/var/log') else logging.NullHandler()
    ]
)

# Don't log sensitive information
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
```

### Monitoring with Prometheus (Optional)
```yaml
# prometheus-config.yml
scrape_configs:
  - job_name: 'justifi-mcp'
    static_configs:
      - targets: ['justifi-mcp-service:8080']
    metrics_path: '/health'
    scrape_interval: 30s
```

## 🚀 Production Checklist

### Pre-Deployment
- [ ] JustiFi production API credentials obtained
- [ ] Environment variables configured securely
- [ ] Container image built and scanned for vulnerabilities
- [ ] Network security policies configured
- [ ] Monitoring and alerting set up

### Deployment
- [ ] Deploy to staging environment first
- [ ] Run full test suite
- [ ] Verify AI client connectivity
- [ ] Test all JustiFi payment operations
- [ ] Monitor logs for errors

### Post-Deployment
- [ ] Configure backup strategy
- [ ] Set up log rotation
- [ ] Document rollback procedures
- [ ] Train team on troubleshooting
- [ ] Schedule regular security updates

## 🆘 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker logs <container-id>

# Verify environment variables
docker exec -it <container-id> env | grep JUSTIFI

# Test connectivity
docker exec -it <container-id> python -c "from tools.justifi import JustiFiClient; print('OK')"
```

**AI client can't connect**
```bash
# Verify MCP server is responding
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | python main.py

# Check file permissions
ls -la main.py
chmod +x main.py

# Verify Python path
which python
python --version
```

**JustiFi API errors**
```bash
# Test credentials
curl -X POST https://api.justifi.ai/v1/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET"

# Check API status
curl -I https://api.justifi.ai/v1/health
```

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=/app python main.py --debug

# Test individual tools
python -c "
import asyncio
from tools.justifi import list_payments
result = asyncio.run(list_payments(limit=1))
print(result)
"
```

## 📞 Support

- **Technical Issues**: Open GitHub issue
- **Security Concerns**: Contact security team
- **JustiFi API**: Contact JustiFi support
- **Deployment Help**: Check troubleshooting section above

---

**Remember**: Each customer should run their own isolated instance for maximum security and compliance. 