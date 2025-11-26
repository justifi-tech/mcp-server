# OAuth 2.1 Implementation Plan for JustiFi MCP Server

> ⚠️ **DO NOT COMMIT THIS FILE TO THE REPOSITORY**
>
> This document contains internal planning details and should remain local only.

---

## Executive Summary

Implement official MCP OAuth 2.1 specification with Auth0 integration. End result: Users add just `{"url": "https://mcp.justifi.ai"}` to their Claude Desktop config, and OAuth flow happens automatically in browser. Zero manual token management.

## Current Architecture

**stdio mode (local dev):**
```
Claude Desktop → stdio pipe → MCP Server → JustiFi API
                              (client_id/secret from .env)
```

**Target architecture (remote):**
```
Claude Desktop → HTTP → MCP Server → JustiFi API
                 (OAuth 2.1)    (token passthrough)
```

---

## User Experience Goal

### Customer Employee Setup
```json
// ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "justifi": {
      "url": "https://mcp.justifi.ai"
    }
  }
}
```

**First tool use:**
1. Claude makes unauthenticated request
2. MCP server returns 401 with OAuth metadata
3. Claude automatically opens browser to Auth0
4. User logs in with JustiFi credentials
5. Auth0 redirects back with authorization code
6. Claude exchanges code for token (PKCE)
7. Claude retries request with token
8. Token stored and auto-refreshed

**User never sees or manages token.**

---

## Phase 1: OAuth Metadata Endpoint

### 1.1 Create Metadata Handler
**NEW FILE**: `modelcontextprotocol/oauth_metadata.py`

```python
def get_protected_resource_metadata(config) -> dict:
    """Return OAuth 2.0 Protected Resource Metadata per RFC 9728."""
    return {
        "authorization_servers": [
            {
                "issuer": f"https://{config.auth0_domain}"
            }
        ],
        "scopes_supported": config.oauth_scopes
    }
```

### 1.2 Update Configuration
**MODIFY**: `python/config.py`

Add fields:
```python
class JustiFiConfig(BaseModel):
    # ... existing fields ...

    # OAuth 2.1 with Auth0
    auth0_domain: str = Field(
        default_factory=lambda: os.getenv("JUSTIFI_AUTH0_DOMAIN", "justifi.us.auth0.com")
    )
    auth0_audience: str = Field(
        default_factory=lambda: os.getenv("JUSTIFI_AUTH0_AUDIENCE", "https://api.justifi.ai")
    )
    oauth_scopes: list[str] = Field(
        default_factory=lambda: os.getenv("JUSTIFI_OAUTH_SCOPES", "").split(",")
    )
```

### 1.3 Register Metadata Route
**MODIFY**: `modelcontextprotocol/server.py`

```python
from .oauth_metadata import get_protected_resource_metadata

@mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
async def oauth_metadata(request: Request) -> JSONResponse:
    config = JustiFiConfig()
    metadata = get_protected_resource_metadata(config)
    return JSONResponse(metadata)
```

**Important**: No authentication required on this endpoint per MCP spec.

---

## Phase 2: OAuth Middleware

### 2.1 Create Auth Middleware
**NEW FILE**: `modelcontextprotocol/middleware/oauth.py`

```python
from fastapi import Request, Response
from fastapi.responses import JSONResponse

class OAuthMiddleware:
    """Extract OAuth bearer token and return 401 if missing."""

    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in ["/.well-known/oauth-protected-resource", "/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")

        # Check for Bearer token (customer OAuth flow)
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            request.state.bearer_token = token
            request.state.auth_type = "oauth"
            return await call_next(request)

        # Check for client credentials (internal dev bypass)
        if "X-Client-Id" in request.headers and "X-Client-Secret" in request.headers:
            request.state.client_id = request.headers["X-Client-Id"]
            request.state.client_secret = request.headers["X-Client-Secret"]
            request.state.auth_type = "client_credentials"
            return await call_next(request)

        # No valid auth - return 401 with OAuth metadata location
        return Response(
            status_code=401,
            headers={
                "WWW-Authenticate": 'Bearer resource_metadata="https://mcp.justifi.ai/.well-known/oauth-protected-resource"'
            }
        )
```

### 2.2 Register Middleware
**MODIFY**: `modelcontextprotocol/server.py`

```python
def create_mcp_server() -> FastMCP:
    mcp = FastMCP("JustiFi Payment Server")

    # Add OAuth middleware for HTTP transport
    if os.getenv("MCP_TRANSPORT") == "http":
        from .middleware.oauth import OAuthMiddleware
        mcp.add_middleware(OAuthMiddleware)

    # ... rest of server setup
```

---

## Phase 3: Token Passthrough

### 3.1 Update JustiFiClient
**MODIFY**: `python/core.py`

```python
class JustiFiClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        bearer_token: str | None = None,
        base_url: str | None = None
    ):
        """
        Initialize JustiFi API client.

        Args:
            client_id: OAuth2 client ID (for service accounts)
            client_secret: OAuth2 client secret (for service accounts)
            bearer_token: Pre-obtained bearer token (from MCP OAuth flow)
            base_url: JustiFi API base URL
        """
        # Validation: must have either client creds OR bearer token
        has_creds = client_id and client_secret
        has_bearer = bearer_token

        if not (has_creds or has_bearer):
            raise AuthenticationError(
                "Must provide either client_id+client_secret or bearer_token"
            )

        self.bearer_token = bearer_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = self._normalize_base_url(base_url)
        self._token_cache = _TokenCache()

    async def get_access_token(self) -> str:
        """Get access token for API requests."""
        if self.bearer_token:
            # OAuth 2.1 token from MCP client - pass through directly
            # JustiFi API will validate it
            return self.bearer_token

        # Client credentials flow (existing code)
        if self._token_cache.is_expired():
            token_data = await self._fetch_oauth_token()
            self._token_cache.token = token_data["access_token"]
            self._token_cache.expires_at = time.time() + token_data["expires_in"] - 60

        return self._token_cache.token
```

### 3.2 Per-Request Client Creation
**MODIFY**: Tool functions in `python/tools/*.py`

Example pattern for all tools:

```python
@mcp.tool()
async def list_payments(
    request: Request,
    limit: int = 25,
    after_cursor: str | None = None,
    before_cursor: str | None = None
) -> dict:
    """List payments with pagination."""

    # Create client from request auth context
    if request.state.auth_type == "oauth":
        client = JustiFiClient(bearer_token=request.state.bearer_token)
    else:
        client = JustiFiClient(
            client_id=request.state.client_id,
            client_secret=request.state.client_secret
        )

    # Rest of tool implementation
    result = await client.request("GET", "/v1/payments", params={...})
    return result
```

**Action**: Update all tool functions in:
- `python/tools/payments.py`
- `python/tools/payouts.py`
- `python/tools/refunds.py`
- `python/tools/disputes.py`
- `python/tools/checkouts.py`
- `python/tools/balances.py`
- `python/tools/payment_methods.py`
- `python/tools/payment_method_groups.py`
- `python/tools/sub_accounts.py`
- `python/tools/terminals.py`
- `python/tools/proceeds.py`
- `python/tools/payments_create.py`
- `python/tools/checkouts_create.py`
- `python/tools/payment_intents.py`
- `python/tools/code_generators.py`

---

## Phase 4: HTTP Transport & Health Check

### 4.1 Update Transport Configuration
**MODIFY**: `modelcontextprotocol/main.py`

```python
def main():
    """Main entry point for FastMCP server."""
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    load_dotenv()

    # Create server
    mcp = create_mcp_server()

    # Load transport config
    config = MCPConfig.from_env()

    # Run with appropriate transport
    if config.transport == "stdio":
        mcp.run()
    elif config.transport == "http":
        mcp.run(transport="http", host=config.host, port=config.port)
    else:
        raise ValueError(f"Unknown transport: {config.transport}")
```

### 4.2 Add Health Check Endpoint
**MODIFY**: `modelcontextprotocol/server.py`

```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    """Health check endpoint for ALB."""
    return PlainTextResponse("OK")
```

---

## Phase 5: Docker & AWS Deployment

### 5.1 Create Dockerfile
**NEW FILE**: `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run server
CMD ["uv", "run", "uvicorn", "modelcontextprotocol.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 5.2 AWS Infrastructure
**NEW DIRECTORY**: `infrastructure/aws/`

Create Terraform configuration for:

**ECS Fargate Cluster:**
- Task definition: 512 CPU, 1024 MB memory
- Network mode: awsvpc
- Launch type: FARGATE
- Desired count: 3 instances for high availability

**Application Load Balancer:**
- HTTPS listener on port 443
- SSL certificate from AWS Certificate Manager
- Target group:
  - Protocol: HTTP
  - Port: 8080
  - Target type: IP (required for Fargate)
  - Health check path: `/health`
- Sticky sessions:
  - Duration: 86400 seconds (1 day)
  - Cookie name: LB generated
- Connection settings:
  - Idle timeout: 3600 seconds (for long-lived connections)

**Route 53:**
- A record: mcp.justifi.ai → ALB DNS name

**Security Groups:**
- ALB security group:
  - Inbound: 443 from 0.0.0.0/0
  - Outbound: 8080 to ECS security group
- ECS security group:
  - Inbound: 8080 from ALB security group
  - Outbound: 443 to 0.0.0.0/0 (for Auth0 and JustiFi API)

**CloudWatch:**
- Log group: /ecs/justifi-mcp
- Log retention: 30 days
- Alarms:
  - Unhealthy target count
  - High CPU utilization
  - High memory utilization

**AWS Secrets Manager:**
- Secret: justifi-mcp/environment
- Store as JSON:
  ```json
  {
    "JUSTIFI_AUTH0_DOMAIN": "justifi.us.auth0.com",
    "JUSTIFI_AUTH0_AUDIENCE": "https://api.justifi.ai",
    "JUSTIFI_OAUTH_SCOPES": "payments:read,payments:write,payouts:read,...",
    "JUSTIFI_CLIENT_ID": "optional_for_dev_bypass",
    "JUSTIFI_CLIENT_SECRET": "optional_for_dev_bypass"
  }
  ```

### 5.3 Deployment Script
**NEW FILE**: `deploy.sh`

```bash
#!/bin/bash
set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="justifi-mcp-server"
ECS_CLUSTER="justifi-mcp"
ECS_SERVICE="justifi-mcp-service"

# Build Docker image
echo "Building Docker image..."
docker build -t ${ECR_REPOSITORY}:latest .

# Tag for ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
docker tag ${ECR_REPOSITORY}:latest ${ECR_URL}:latest

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_URL}

# Push to ECR
echo "Pushing to ECR..."
docker push ${ECR_URL}:latest

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service \
  --cluster ${ECS_CLUSTER} \
  --service ${ECS_SERVICE} \
  --force-new-deployment \
  --region ${AWS_REGION}

echo "Deployment initiated. Waiting for service to stabilize..."
aws ecs wait services-stable \
  --cluster ${ECS_CLUSTER} \
  --services ${ECS_SERVICE} \
  --region ${AWS_REGION}

echo "Deployment complete!"
```

---

## Phase 6: Testing

### 6.1 Local OAuth Testing
Use ngrok to test OAuth flow locally:

```bash
# Terminal 1: Start MCP server
MCP_TRANSPORT=http MCP_PORT=8080 python main.py

# Terminal 2: Start ngrok
ngrok http 8080

# Update Auth0 callback URLs to include ngrok URL
# Test with Claude Desktop pointing to ngrok URL
```

### 6.2 Unit Tests
**NEW FILE**: `tests/test_oauth_middleware.py`

```python
import pytest
from fastapi import Request
from modelcontextprotocol.middleware.oauth import OAuthMiddleware

class TestOAuthMiddleware:
    def test_returns_401_without_auth(self):
        """Test that requests without auth return 401."""
        # Implementation

    def test_www_authenticate_header_format(self):
        """Test WWW-Authenticate header is correct format."""
        # Implementation

    def test_bearer_token_extraction(self):
        """Test bearer token is extracted and stored in request state."""
        # Implementation

    def test_client_credentials_bypass(self):
        """Test X-Client-Id/Secret headers work for devs."""
        # Implementation

    def test_public_endpoints_skip_auth(self):
        """Test /health and /.well-known/* don't require auth."""
        # Implementation
```

**NEW FILE**: `tests/test_oauth_metadata.py`

```python
import pytest
from modelcontextprotocol.oauth_metadata import get_protected_resource_metadata

class TestOAuthMetadata:
    def test_metadata_structure(self):
        """Test metadata has correct structure per RFC 9728."""
        # Implementation

    def test_scopes_included(self):
        """Test all configured scopes are in scopes_supported."""
        # Implementation

    def test_authorization_servers_format(self):
        """Test authorization_servers has issuer field."""
        # Implementation
```

### 6.3 Integration Tests
**NEW FILE**: `tests/test_oauth_integration.py`

```python
class TestOAuthIntegration:
    def test_end_to_end_oauth_flow(self):
        """Test complete OAuth flow with mocked Auth0."""
        # Mock Auth0 endpoints
        # Make unauthenticated request
        # Verify 401 response
        # Follow OAuth flow
        # Make authenticated request
        # Verify success

    def test_token_passthrough_to_justifi(self):
        """Test bearer token is passed to JustiFi API."""
        # Implementation

    def test_invalid_token_from_justifi(self):
        """Test 401 from JustiFi API is returned to client."""
        # Implementation
```

---

## Phase 7: Documentation

### 7.1 Update README
**MODIFY**: `README.md`

Add section:

```markdown
## Authentication

### OAuth 2.1 (Recommended for End Users)

JustiFi MCP Server uses OAuth 2.1 with PKCE for secure, user-friendly authentication.

**Setup for Claude Desktop:**

1. Open your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add JustiFi MCP server:
   ```json
   {
     "mcpServers": {
       "justifi": {
         "url": "https://mcp.justifi.ai"
       }
     }
   }
   ```

3. Restart Claude Desktop

4. When you first use a JustiFi tool, Claude will automatically open your browser to log in

5. Sign in with your JustiFi credentials

6. Done! Token is managed automatically

### Client Credentials (For Internal Development)

Developers can use client credentials for local testing:

```bash
export JUSTIFI_CLIENT_ID="your_client_id"
export JUSTIFI_CLIENT_SECRET="your_client_secret"
python main.py
```

Or with HTTP transport using headers:

```bash
curl -X POST https://mcp.justifi.ai/mcp/list_payments \
  -H "X-Client-Id: your_client_id" \
  -H "X-Client-Secret: your_client_secret"
```
```

### 7.2 Customer Setup Guide
**NEW FILE**: `docs/customer-setup.md`

```markdown
# Setting Up JustiFi MCP Server

## For Claude Desktop Users

### Prerequisites
- Active JustiFi account with dashboard access
- Claude Desktop installed

### One-Time Setup

1. **Open Claude Desktop Configuration**

   Location depends on your OS:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add JustiFi Server**

   Add this to the `mcpServers` object:
   ```json
   {
     "mcpServers": {
       "justifi": {
         "url": "https://mcp.justifi.ai"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **First Tool Use**

   When you first use any JustiFi tool (e.g., "list my recent payments"):
   - Claude will automatically open your browser
   - You'll be taken to the JustiFi login page
   - Sign in with your JustiFi credentials
   - Browser will show "Authorization successful, return to Claude"
   - Return to Claude Desktop

5. **Done!**

   Your authentication token is now stored and will be automatically refreshed.

### For Cursor Users

Similar setup in Cursor's MCP configuration.

### Troubleshooting

**Browser doesn't open:**
- Check your system's default browser settings
- Try manually opening the authorization URL shown in Claude

**Login fails:**
- Verify you have access to the JustiFi dashboard at app.justifi.ai
- Contact your JustiFi administrator if you don't have access

**Token expired:**
- Claude will automatically prompt you to re-authorize
- This typically happens after 7 days
```

### 7.3 Developer Setup Guide
**NEW FILE**: `docs/developer-setup.md`

```markdown
# Developer Setup

## Local Development

### Prerequisites
- Python 3.12+
- uv package manager
- JustiFi API client credentials

### Setup

1. **Clone and Install**
   ```bash
   git clone https://github.com/justifi/mcp-server.git
   cd mcp-server
   make setup
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   JUSTIFI_CLIENT_ID=your_client_id
   JUSTIFI_CLIENT_SECRET=your_client_secret
   ```

3. **Run Tests**
   ```bash
   make test
   ```

4. **Start Server (stdio mode)**
   ```bash
   python main.py
   ```

## Testing OAuth Flow Locally

To test the OAuth flow locally with Claude Desktop:

1. **Start ngrok tunnel**
   ```bash
   ngrok http 8080
   ```

2. **Start MCP server in HTTP mode**
   ```bash
   MCP_TRANSPORT=http MCP_PORT=8080 python main.py
   ```

3. **Update Auth0 callback URLs**

   Add ngrok URL to allowed callbacks in Auth0 dashboard

4. **Configure Claude Desktop**
   ```json
   {
     "mcpServers": {
       "justifi-local": {
         "url": "https://your-ngrok-url.ngrok.io"
       }
     }
   }
   ```

5. **Test OAuth flow**

   Use JustiFi tools in Claude, verify browser opens and login works

## Using Client Credentials in HTTP Mode

For testing without OAuth:

```bash
curl -X POST https://mcp.justifi.ai/mcp/list_payments \
  -H "X-Client-Id: your_client_id" \
  -H "X-Client-Secret: your_client_secret" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```
```

### 7.4 Deployment Guide
**NEW FILE**: `docs/deployment.md`

```markdown
# Deployment Guide

## AWS ECS Fargate Deployment

### Prerequisites
- AWS account with appropriate permissions
- AWS CLI configured
- Terraform or AWS CDK installed
- Docker installed locally

### Infrastructure Setup

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name justifi-mcp-server
   ```

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure/aws
   terraform init
   terraform plan
   terraform apply
   ```

3. **Configure Secrets**
   ```bash
   aws secretsmanager create-secret \
     --name justifi-mcp/environment \
     --secret-string '{
       "JUSTIFI_AUTH0_DOMAIN": "justifi.us.auth0.com",
       "JUSTIFI_AUTH0_AUDIENCE": "https://api.justifi.ai",
       "JUSTIFI_OAUTH_SCOPES": "payments:read,payments:write,..."
     }'
   ```

4. **Deploy Application**
   ```bash
   ./deploy.sh
   ```

### Monitoring

- CloudWatch Logs: `/ecs/justifi-mcp`
- CloudWatch Alarms: Check ECS console
- Health check: `curl https://mcp.justifi.ai/health`

### Updating

To deploy a new version:

```bash
./deploy.sh
```

This will build, push, and trigger a rolling update of ECS tasks.
```

### 7.5 Scope Documentation
**NEW FILE**: `docs/scopes.md`

```markdown
# OAuth Scopes

## Available Scopes

[List your actual scopes here]

Example structure:

| Scope | Description | Required For Tools |
|-------|-------------|-------------------|
| `payments:read` | Read payment information | `list_payments`, `retrieve_payment` |
| `payments:write` | Create and modify payments | `create_payment`, `refund_payment` |
| `payouts:read` | Read payout information | `list_payouts`, `retrieve_payout` |
| `checkouts:read` | Read checkout information | `list_checkouts`, `retrieve_checkout` |
| `checkouts:write` | Create checkouts | `create_checkout` |
| ... | ... | ... |

## Scope Requirements by Tool

### Payment Tools
- `list_payments`: requires `payments:read`
- `retrieve_payment`: requires `payments:read`
- `create_payment`: requires `payments:write`

[Complete the list based on your actual tools and scopes]

## Requesting Scopes

When Claude Desktop initiates the OAuth flow, it will request all scopes listed in `scopes_supported` from the metadata endpoint. Users will see these scopes on the Auth0 consent screen.

To limit scopes for testing, set the `JUSTIFI_OAUTH_SCOPES` environment variable:

```bash
export JUSTIFI_OAUTH_SCOPES="payments:read,payouts:read"
```
```

---

## Phase 8: Auth0 Configuration

### 8.1 Configure Auth0 Application

In Auth0 Dashboard:

1. **Navigate to Applications**
   - Select existing JustiFi API application
   - Or create new "Native Application"

2. **Configure Application Settings**
   - Application Type: Native Application
   - Token Endpoint Authentication Method: None (PKCE only)
   - Grant Types:
     - ✅ Authorization Code
     - ✅ Refresh Token
   - Allowed Callback URLs: Add:
     - `http://localhost:*` (for Claude Desktop)
     - `http://127.0.0.1:*` (for Claude Desktop)

3. **Configure Token Settings**
   - Access Token Lifetime: 604800 seconds (7 days)
   - Refresh Token Lifetime: 2592000 seconds (30 days)
   - Refresh Token Rotation: Enabled
   - Refresh Token Expiration: Absolute expiration

4. **Configure API**
   - API Identifier: `https://api.justifi.ai` (must match JUSTIFI_AUTH0_AUDIENCE)
   - Signing Algorithm: RS256
   - RBAC Settings: Enable if using role-based access

5. **Configure Scopes**
   - Add all scopes that will be in `JUSTIFI_OAUTH_SCOPES`
   - Ensure scope descriptions are user-friendly (shown on consent screen)

### 8.2 Test Configuration

Use Auth0's API Explorer or curl to test token acquisition:

```bash
# This would be done by Claude automatically, but useful for testing
curl --request POST \
  --url https://justifi.us.auth0.com/oauth/token \
  --header 'content-type: application/x-www-form-urlencoded' \
  --data grant_type=authorization_code \
  --data 'client_id=YOUR_CLIENT_ID' \
  --data code_verifier=VERIFIER \
  --data code=AUTHORIZATION_CODE \
  --data 'redirect_uri=http://localhost:8080/callback'
```

---

## Environment Variables Reference

### Production (Required)

```bash
# Auth0 Configuration
JUSTIFI_AUTH0_DOMAIN=justifi.us.auth0.com
JUSTIFI_AUTH0_AUDIENCE=https://api.justifi.ai
JUSTIFI_OAUTH_SCOPES=payments:read,payments:write,payouts:read,payouts:write,checkouts:read,checkouts:write,refunds:read,refunds:write,disputes:read,balances:read,payment_methods:read,sub_accounts:read,terminals:read,proceeds:read

# Transport Configuration
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8080

# Logging
LOG_LEVEL=INFO
```

### Development (Optional)

```bash
# For internal developer bypass
JUSTIFI_CLIENT_ID=dev_client_id
JUSTIFI_CLIENT_SECRET=dev_client_secret

# For local OAuth testing
JUSTIFI_BASE_URL=https://api.staging.justifi.ai
```

---

## Dependencies to Add

**MODIFY**: `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    "uvicorn[standard]>=0.30.0",  # ASGI server for HTTP transport
]
```

No JWT validation libraries needed - token passthrough only.

---

## Backward Compatibility

✅ **stdio mode** with client credentials continues working unchanged
✅ **HTTP mode** with client credentials via headers (internal devs)
✅ **No breaking changes** to existing tool signatures
✅ **Existing .env** configurations work for local development
✅ **Gradual rollout** - can deploy to production without forcing OAuth

---

## Implementation Checklist

### Phase 1: OAuth Metadata
- [ ] Create `modelcontextprotocol/oauth_metadata.py`
- [ ] Update `python/config.py` with Auth0 fields
- [ ] Register `/.well-known/oauth-protected-resource` route
- [ ] Test metadata endpoint returns correct JSON

### Phase 2: OAuth Middleware
- [ ] Create `modelcontextprotocol/middleware/oauth.py`
- [ ] Implement bearer token extraction
- [ ] Implement 401 response with WWW-Authenticate header
- [ ] Add client credentials bypass for devs
- [ ] Register middleware in server creation
- [ ] Test middleware with various auth scenarios

### Phase 3: Token Passthrough
- [ ] Update `JustiFiClient.__init__()` to accept bearer_token
- [ ] Update `get_access_token()` to handle bearer tokens
- [ ] Update all tool functions to accept Request parameter
- [ ] Update all tools to create per-request clients
- [ ] Test token passthrough to JustiFi API

### Phase 4: HTTP Transport
- [ ] Update default transport configuration
- [ ] Add `/health` endpoint
- [ ] Test HTTP transport locally
- [ ] Test with ngrok and Claude Desktop

### Phase 5: Deployment
- [ ] Create Dockerfile
- [ ] Create Terraform/CDK infrastructure files
- [ ] Create deploy.sh script
- [ ] Set up ECR repository
- [ ] Configure AWS Secrets Manager
- [ ] Deploy to staging
- [ ] Test staging deployment
- [ ] Deploy to production

### Phase 6: Testing
- [ ] Write OAuth middleware tests
- [ ] Write OAuth metadata tests
- [ ] Write integration tests
- [ ] Run full test suite
- [ ] Test with real Auth0 (staging environment)

### Phase 7: Documentation
- [ ] Update README with authentication section
- [ ] Create customer setup guide
- [ ] Create developer setup guide
- [ ] Create deployment guide
- [ ] Create scopes documentation
- [ ] Review all documentation

### Phase 8: Auth0
- [ ] Configure Auth0 application
- [ ] Add callback URLs
- [ ] Configure token lifetimes
- [ ] Configure scopes
- [ ] Test Auth0 configuration
- [ ] Document Auth0 settings

---

## Rollout Strategy

### Week 1: Development & Local Testing
- Implement Phases 1-4
- Test locally with ngrok
- Internal team review

### Week 2: Staging Deployment
- Deploy to AWS staging environment
- Configure staging Auth0 application
- Internal team testing with Claude Desktop
- Fix any issues found

### Week 3: Production Deployment
- Deploy to production (mcp.justifi.ai)
- Configure production Auth0 application
- Internal testing in production
- Monitor logs and metrics

### Week 4: Beta Testing
- Invite 2-3 friendly customers
- Provide setup guide
- Gather feedback
- Monitor usage and errors

### Week 5: General Availability
- Announce to all customers
- Update dashboard with setup instructions
- Monitor support requests
- Iterate on documentation

---

## Success Metrics

### Technical
- [ ] 99.9% uptime on mcp.justifi.ai
- [ ] < 500ms p95 latency for OAuth metadata endpoint
- [ ] < 2s p95 latency for authenticated tool requests
- [ ] Zero token leaks or security incidents
- [ ] 100% token passthrough success rate

### User Experience
- [ ] < 5 minutes from config to first successful tool use
- [ ] < 2% OAuth flow failure rate
- [ ] Zero customer support tickets about "how to get token"
- [ ] Positive customer feedback on ease of setup

### Business
- [ ] 50% of customers adopt MCP integration within 3 months
- [ ] 10+ active users per customer
- [ ] Usage grows month-over-month

---

## Known Limitations & Future Work

### Current Limitations
- Token refresh requires user re-authorization (could be improved with refresh token handling)
- No fine-grained permission system (all scopes requested at once)
- No usage analytics per user (could add logging)

### Future Enhancements
- [ ] Refresh token handling for seamless token renewal
- [ ] Per-tool scope requirements (request only needed scopes)
- [ ] Usage analytics and rate limiting per user
- [ ] Admin dashboard for customer's IT admins
- [ ] Self-service client registration
- [ ] Support for other AI tools (custom SDKs)

---

## Security Considerations

### Token Security
- ✅ Tokens never logged
- ✅ HTTPS only in production
- ✅ Token validation by JustiFi API
- ✅ Short token lifetime (7 days)
- ✅ PKCE prevents interception attacks

### API Security
- ✅ All requests authenticated
- ✅ JustiFi API performs authorization
- ✅ Sub-account scoping at API level
- ✅ No token passthrough to upstream APIs

### Infrastructure Security
- ✅ ALB terminates SSL
- ✅ ECS tasks in private subnets
- ✅ Security groups restrict access
- ✅ Secrets in AWS Secrets Manager
- ✅ CloudWatch logging enabled

---

## Contact & Support

For questions about this implementation:
- Technical lead: [Your name]
- Auth0 admin: [Name]
- AWS admin: [Name]

For Auth0 configuration:
- Dashboard: https://manage.auth0.com

For AWS infrastructure:
- Console: https://console.aws.amazon.com
- Region: us-east-1 (or your region)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-13
**Status**: Planning

> ⚠️ **REMINDER: DO NOT COMMIT THIS FILE TO THE REPOSITORY**
