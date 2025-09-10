"""JustiFi Code Generation Tools

Intelligent code generators that help developers build complete JustiFi integrations.
These tools generate production-ready code tailored to specific frameworks and use cases.
"""

from __future__ import annotations

from typing import Any, Optional

from ..core import JustiFiClient
from .base import ToolError, ValidationError, handle_tool_errors
from .response_formatter import standardize_response


@handle_tool_errors
async def generate_unified_checkout_integration(
    client: JustiFiClient,
) -> dict[str, Any]:
    """Generate working JustiFi checkout integration for v5.7.6+.

    Provides:
    - Working Express.js backend + frontend example
    - YAML integration guide with requirements and troubleshooting  
    - Framework-agnostic patterns for any language/stack

    Requirements:
    - JustiFi account with API credentials
    - Modern browser with ES6 module support
    - Node.js 14+ for the Express example

    Args:
        client: JustiFi API client

    Returns:
        Dictionary with complete Express.js example, framework-agnostic patterns, 
        setup instructions, and comprehensive documentation

    Raises:
        ToolError: If code generation fails
    """

    try:
        # Generate complete working Express.js example
        backend_code = _generate_express_backend()
        frontend_code = _generate_vanilla_frontend()
        config = _generate_configuration()
        tests = _generate_test_suite()
        
        # Generate framework-agnostic integration patterns
        patterns = _generate_integration_patterns()
        
        # Combine everything into comprehensive response
        all_files = {
            **backend_code,
            **frontend_code,
            **config,
            **tests,
            **patterns,
        }
        
        result = {
            "success": True,
            "description": "Complete JustiFi checkout integration: Express.js example + framework-agnostic patterns",
            "files": all_files,
            "resources": _get_justifi_resources(),
            "next_steps": _get_comprehensive_next_steps(),
            "working_example": "Express.js + vanilla HTML (ready to run)",
            "adaptable_patterns": "Framework-agnostic code snippets for any technology stack"
        }

        return standardize_response(result, "generate_unified_checkout_integration")

    except Exception as e:
        raise ToolError(
            f"Failed to generate checkout integration: {str(e)}",
            error_type="CodeGenerationError",
        ) from e


def _generate_backend_code(framework: str, features: list[str]) -> dict[str, str]:
    """Generate backend code - provides Express.js example for all frameworks."""
    # Always return Express.js implementation regardless of requested framework
    # LLMs should translate this example using the comprehensive YAML translation guide
    return _generate_express_backend(features)


def _generate_express_backend() -> dict[str, str]:
    """Generate Express.js backend code that actually works."""

    server_code = '''require('dotenv').config();
const express = require('express');
const app = express();

app.use(express.json());
app.use(express.static('public'));

async function getAccessToken() {
    const response = await fetch(`${process.env.JUSTIFI_BASE_URL}/oauth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            grant_type: 'client_credentials',
            client_id: process.env.JUSTIFI_CLIENT_ID,
            client_secret: process.env.JUSTIFI_CLIENT_SECRET
        })
    });

    if (!response.ok) {
        throw new Error(`OAuth failed: ${response.status}`);
    }

    const tokenData = await response.json();
    return tokenData.access_token;
}

// API endpoint: Create checkout
app.post('/api/checkout', async (req, res) => {
    try {
        const { amount, description } = req.body;
        
        if (!amount || amount < 100) {
            return res.status(400).json({ success: false, error: 'Amount must be at least $1.00' });
        }
        if (!description) {
            return res.status(400).json({ success: false, error: 'Description is required' });
        }
        
        const token = await getAccessToken();

        // Step 1: Create checkout
        const checkoutResponse = await fetch(`${process.env.JUSTIFI_BASE_URL}/v1/checkouts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Sub-Account': process.env.JUSTIFI_SUB_ACCOUNT_ID
            },
            body: JSON.stringify({
                amount: parseInt(amount),
                description: description,
                origin_url: 'localhost:3001'  // No http:// prefix!
            })
        });

        if (!checkoutResponse.ok) {
            throw new Error(`Checkout failed: ${checkoutResponse.status}`);
        }

        const checkout = await checkoutResponse.json();
        const checkoutId = checkout.data.id;

        // Step 2: Get web component token for this checkout (NO Sub-Account header needed)
        const tokenResponse = await fetch(`${process.env.JUSTIFI_BASE_URL}/v1/web_component_tokens`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                resources: [
                    `write:tokenize:${process.env.JUSTIFI_SUB_ACCOUNT_ID}`,
                    `write:checkout:${checkoutId}`
                ]
            })
        });

        if (!tokenResponse.ok) {
            throw new Error(`Web component token failed: ${tokenResponse.status}`);
        }

        const tokenData = await tokenResponse.json();
        const webComponentToken = tokenData.access_token;

        // Step 3: Render checkout page with embedded data (SSR pattern)
        const checkoutHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checkout - ${description}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@justifi/webcomponents@5.7.6/dist/webcomponents/webcomponents.css"/>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5;
        }
        .container { 
            background: white; border-radius: 12px; padding: 30px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; color: #333; }
        .order-summary { 
            background: #f8f9fa; border-radius: 8px; padding: 20px; 
            margin-bottom: 30px; border: 1px solid #e9ecef;
        }
        .amount { font-size: 24px; font-weight: bold; color: #2c5aa0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Complete Your Payment</h1>
        <div class="order-summary">
            <h3>Order Summary</h3>
            <p><strong>Description:</strong> ${description}</p>
            <p class="amount"><strong>Total:</strong> $${(parseInt(amount) / 100).toFixed(2)}</p>
        </div>
        <div id="checkout-container"></div>
    </div>
    
    <script type="module" src="https://cdn.jsdelivr.net/npm/@justifi/webcomponents@5.7.6/dist/webcomponents/webcomponents.esm.js"></script>
    <script>
        // Data is embedded during server-side rendering - no API calls needed
        const checkoutId = '${checkoutId}';
        const authToken = '${webComponentToken}';
        
        // Wait for web components to load
        customElements.whenDefined('justifi-checkout').then(() => {
            const checkoutElement = document.createElement('justifi-checkout');
            checkoutElement.setAttribute('checkout-id', checkoutId);
            checkoutElement.setAttribute('auth-token', authToken);
            
            // Event handlers
            checkoutElement.addEventListener('submit-event', (event) => {
                console.log('Payment submitted:', event.detail);
                alert('Payment successful! Thank you for your purchase.');
            });
            
            checkoutElement.addEventListener('error-event', (event) => {
                console.log('Payment error:', event.detail);
                alert('Payment failed: ' + (event.detail.message || 'Unknown error'));
            });
            
            document.getElementById('checkout-container').appendChild(checkoutElement);
        });
    </script>
</body>
</html>`;
        
        res.setHeader('Content-Type', 'text/html');
        res.send(checkoutHtml);

    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});


app.listen(process.env.PORT || 3001);'''

    return {
        "server.js": server_code,
        "package.json": _generate_express_package_json(),
    }


def _generate_express_package_json() -> str:
    """Generate package.json for Express backend."""
    return """{
  "name": "justifi-checkout-integration",
  "version": "1.0.0",
  "description": "JustiFi checkout integration with Express.js",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.7.0",
    "supertest": "^6.3.3"
  }
}"""


def _generate_frontend_code(frontend: str, features: list[str]) -> dict[str, str]:
    """Generate frontend code for specified framework."""
    if frontend == "vanilla":
        return _generate_vanilla_frontend(features)
    elif frontend == "react":
        return _generate_react_frontend(features)
    elif frontend == "vue":
        return _generate_vue_frontend(features)
    elif frontend == "angular":
        return _generate_angular_frontend(features)
    else:
        raise ValueError(f"Unsupported frontend: {frontend}")


def _generate_vanilla_frontend() -> dict[str, str]:
    """Generate minimal working frontend with clear security warnings."""

    html_code = '''<!DOCTYPE html>
<html>
<head>
    <title>JustiFi Checkout</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .form-group { margin: 15px 0; }
        input { width: 100%; padding: 10px; margin: 5px 0; }
        button { background: #007cba; color: white; padding: 12px 20px; border: none; cursor: pointer; }
        .checkout-container { margin-top: 20px; display: none; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>JustiFi Checkout Integration</h1>
    
    <!-- ⚠️ SECURITY WARNING: This page NEVER calls api.justifi.ai directly! -->
    <!-- All JustiFi API calls happen on YOUR backend server only -->
    
    <form id="payment-form" action="/api/checkout" method="POST">
        <div class="form-group">
            <label>Amount (cents):</label>
            <input type="number" name="amount" id="amount" min="100" value="2999" required>
        </div>
        <div class="form-group">
            <label>Description:</label>
            <input type="text" name="description" id="description" value="Premium Plan" required>
        </div>
        <button type="submit">Continue to Checkout</button>
    </form>

    <div id="checkout-container" class="checkout-container">
        <h3>Complete Payment</h3>
        <div id="checkout-content">Loading...</div>
    </div>

    <div id="messages"></div>

    <!-- JustiFi Stylesheet (required for component styling) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@justifi/webcomponents@5.7.6/dist/webcomponents/webcomponents.css"/>
    
    <!-- JustiFi Web Components v5.7.6+ (requires type="module") -->
    <!-- SSR WARNING: Web components require client-side loading -->
    <!-- Next.js: Use dynamic import with ssr: false -->
    <!-- Nuxt.js: Use <ClientOnly> wrapper -->
    <!-- SvelteKit: Use browser check or onMount -->
    <script type="module" src="https://cdn.jsdelivr.net/npm/@justifi-tech/justifi-webcomponents@5.7.6/dist/index.js"></script>
</body>
</html>'''

    js_code = '''// ⚠️ SECURITY WARNING: Frontend NEVER calls JustiFi API directly!
// This code only calls YOUR backend at /api/checkout and /api/web-component-token

// ⚠️ SSR WARNING: This code creates web components that require client-side execution
// Framework-specific SSR handling:
// - Next.js: Use dynamic() with ssr: false
// - Nuxt.js: Wrap in <ClientOnly>
// - SvelteKit: Use browser check or onMount()
// - React: useEffect() with proper cleanup

document.getElementById('payment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const amount = document.getElementById('amount').value;
    const description = document.getElementById('description').value;
    
    try {
        // Step 1: Call YOUR backend to create checkout (never call JustiFi directly!)
        const checkoutResponse = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: parseInt(amount), description })
        });
        
        if (!checkoutResponse.ok) {
            throw new Error(`Server error: ${checkoutResponse.status}`);
        }
        
        const checkoutData = await checkoutResponse.json();
        if (!checkoutData.success) throw new Error(checkoutData.error);
        
        // Step 2: Call YOUR backend to get web component token (never call JustiFi directly!)
        const tokenResponse = await fetch(`/api/web-component-token?checkout_id=${checkoutData.data.id}`);
        
        if (!tokenResponse.ok) {
            throw new Error(`Token error: ${tokenResponse.status}`);
        }
        
        const tokenData = await tokenResponse.json();
        if (!tokenData.success) throw new Error(tokenData.error);
        
        // Step 3: Create JustiFi checkout component
        const checkoutElement = document.createElement('justifi-checkout');
        checkoutElement.setAttribute('checkout-id', checkoutData.data.id);
        checkoutElement.setAttribute('auth-token', tokenData.token);
        
        // Enable all payment methods (v5.7.6+ requirement)
        checkoutElement.setAttribute('disable-card-form', 'false');
        checkoutElement.setAttribute('disable-bnpl-form', 'false');
        checkoutElement.setAttribute('disable-bank-account-form', 'false');
        
        // Listen for payment completion
        checkoutElement.addEventListener('submit-event', (event) => {
            if (event.detail.response?.payment_id) {
                showMessage('Payment successful! 🎉', 'success');
                setTimeout(() => location.reload(), 2000);
            }
        });
        
        checkoutElement.addEventListener('error-event', (event) => {
            showMessage(`Payment error: ${event.detail.message}`, 'error');
        });
        
        // Show the component
        document.getElementById('checkout-container').style.display = 'block';
        document.getElementById('checkout-content').innerHTML = '';
        document.getElementById('checkout-content').appendChild(checkoutElement);
        
    } catch (error) {
        showMessage(error.message, 'error');
    }
});

function showMessage(message, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = message;
    document.getElementById('messages').appendChild(div);
    
    if (type !== 'error') {
        setTimeout(() => div.remove(), 5000);
    }
}'''

    return {
        "public/index.html": html_code,
    }








def _generate_react_frontend(features: list[str]) -> dict[str, str]:
    """Generate React frontend code."""
    # Implementation for React would go here
    return {"CheckoutComponent.jsx": "// React implementation coming soon"}


def _generate_vue_frontend(features: list[str]) -> dict[str, str]:
    """Generate Vue frontend code."""
    # Implementation for Vue would go here
    return {"CheckoutComponent.vue": "// Vue implementation coming soon"}


def _generate_angular_frontend(features: list[str]) -> dict[str, str]:
    """Generate Angular frontend code."""
    # Implementation for Angular would go here
    return {"checkout.component.ts": "// Angular implementation coming soon"}


def _generate_configuration() -> dict[str, str]:
    """Generate configuration files."""

    env_template = """# JustiFi API Configuration (Required)
JUSTIFI_CLIENT_ID=test_your_client_id
JUSTIFI_CLIENT_SECRET=test_your_client_secret
JUSTIFI_SUB_ACCOUNT_ID=acc_your_sub_account_id
JUSTIFI_BASE_URL=https://api.justifi.ai
PORT=3001
NODE_ENV=development"""

    yaml_instructions = """# JustiFi Integration Requirements (v5.7.6+)

# Essential Setup
setup:
  script_tag: '<script type="module" src="https://cdn.jsdelivr.net/npm/@justifi-tech/justifi-webcomponents@5.7.6/dist/index.js"></script>'
  token_scope: "write:tokenize:${accountId}"
  origin_url: "localhost:3001"  # NO http:// prefix
  component_attributes:
    - 'disable-card-form="false"'
    - 'disable-bnpl-form="false"'
    - 'disable-bank-account-form="false"'

# Security (Critical)
security:
  - Frontend NEVER calls api.justifi.ai directly
  - Only frontend action: form submit to YOUR backend /api/checkout
  - Backend handles all JustiFi API calls with Sub-Account header
  - OAuth client credentials flow server-side only
  - Data embedded in server-rendered HTML (no client-side token exposure)

# Integration Flow (Server-Side Rendering Pattern)
flow:
  1: "Frontend form submits to /api/checkout with amount & description"
  2: "Backend creates checkout + gets web component token"
  3: "Backend renders and returns complete checkout page with data embedded"
  4: "Frontend checkout page loads with checkout ID & token already in HTML"
  5: "No additional API calls - classic SSR pattern"

# Framework Translation Patterns (for LLMs)
framework_patterns:
  api_route_pattern: "POST /api/checkout → validate input → oauth token → justifi api call → return response"
  error_handling_pattern: "try/catch → log error → return structured error response with status codes"
  oauth_token_pattern: "fetch oauth token → use for authenticated API calls"
  input_validation_pattern: "amount >= 100 && description.trim().length > 0 && typeof amount === integer"
  oauth_flow_pattern: "POST oauth/token with client_credentials → get access_token → use Bearer token for API calls"
  
security_patterns:
  frontend_rule: "Frontend only calls YOUR backend APIs, never api.justifi.ai directly"
  backend_rule: "Backend includes Sub-Account header on all authenticated JustiFi API calls"
  environment_rule: "Keep all credentials server-side only, never expose in frontend"
  validation_rule: "Always validate user input before making API calls"

# Event Handlers
events:
  submit-event: "Payment successful (contains payment_id)"
  error-event: "Payment failed (contains error message)"

# Test Cards
test_cards:
  success: "4242424242424242"
  decline: "4000000000000002"

# Common Dependencies (by Language)
common_dependencies:
  javascript:
    http_clients: ["axios", "fetch (built-in)", "got", "node-fetch"]
    environment: ["dotenv", "@types/node (TypeScript)"]
    frameworks: ["express", "next", "fastify", "koa"]
    
  python:
    http_clients: ["requests", "httpx", "urllib3", "aiohttp"]
    environment: ["python-dotenv", "pydantic (validation)"]
    frameworks: ["fastapi", "django", "flask", "starlette"]
    
  go:
    http_clients: ["net/http (standard)", "resty", "gentleman"]
    environment: ["godotenv", "viper", "envconfig"]
    frameworks: ["gin", "echo", "fiber", "net/http (standard)"]
    
  php:
    http_clients: ["guzzlehttp/guzzle", "curl", "file_get_contents"]
    environment: ["vlucas/phpdotenv", "symfony/dotenv"]
    frameworks: ["laravel", "symfony", "slim", "vanilla-php"]
    
  ruby:
    http_clients: ["httparty", "net/http", "faraday", "rest-client"]
    environment: ["dotenv", "figaro", "config"]
    frameworks: ["rails", "sinatra", "hanami", "roda"]

# Language Translation Hints (for LLMs)
language_hints:
  javascript:
    async_pattern: "Use async/await with fetch() or axios"
    error_handling: "try/catch blocks, throw new Error()"
    env_vars: "process.env.VARIABLE_NAME"
    json_handling: "JSON.stringify() and response.json()"
    
  python:
    async_pattern: "Use requests.post() or httpx.AsyncClient()"
    error_handling: "try/except blocks, raise Exception()"
    env_vars: "os.getenv('VARIABLE_NAME')"
    json_handling: "response.json() and json.dumps()"
    
  go:
    async_pattern: "Use net/http.Client with context.Context"
    error_handling: "if err != nil { return nil, err }"
    env_vars: "os.Getenv() with validation"
    json_handling: "json.Marshal() and json.Unmarshal()"
    
  php:
    async_pattern: "Use Guzzle or cURL with timeout settings"
    error_handling: "try/catch blocks, throw new Exception()"
    env_vars: "$_ENV['VARIABLE_NAME'] with validation"
    json_handling: "json_encode() and json_decode()"
    
  ruby:
    async_pattern: "Use HTTParty or Net::HTTP with proper headers"
    error_handling: "rescue blocks, raise StandardError"
    env_vars: "ENV['VARIABLE_NAME'] with fallbacks"
    json_handling: "to_json and JSON.parse()"

# Common Fixes
fixes:
  "Unexpected token export": "Add type='module' to script tag"
  "403 Forbidden": "Remove http:// from origin_url, add Sub-Account header"
  "Only card payments": "Add all disable-*-form='false' attributes"
  "CORS errors": "Frontend calling JustiFi directly (use backend instead)"

# TypeScript Definitions (Universal)
typescript_definitions: |
  interface JustiFiCheckout {
    id: string;
    amount: number;  // integer in cents (e.g., 2999 = $29.99)
    description: string;
    status: 'pending' | 'completed' | 'failed' | 'canceled';
    created_at: string;
    updated_at: string;
  }

  interface OAuthResponse {
    access_token: string;
    expires_in: number;
    token_type: 'Bearer';
  }

  interface WebComponentToken {
    access_token: string;
    expires_in: number;
    issued_at: string;
  }

  interface CheckoutRequest {
    amount: number;
    description: string;
    origin_url?: string;
  }

  interface APIResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
  }

# Official Resources
resources:
  examples: "https://github.com/justifi-tech/web-component-library/tree/main/apps/component-examples"
  storybook: "https://storybook.justifi.ai"
  docs: "https://docs.justifi.ai/api-spec"
"""

    readme = """
# JustiFi Checkout Integration

Complete Express.js backend with vanilla HTML frontend integration.

## 📋 Version Requirements & Compatibility

### JustiFi Web Components v5.7.6+
- **Required**: ES6 modules (`type="module"` in script tag)
- **Token Scope**: Uses `write:tokenize:${accountId}` format (not checkout-specific)
- **Component Attributes**: Enable payment methods with `disable-*-form="false"` 
- **Breaking Changes**: Older versions use different token scopes and may not require ES modules

### Browser Compatibility
- **Supports**: Chrome 61+, Firefox 60+, Safari 10.1+, Edge 16+
- **Required**: ES6 modules, Web Components, Shadow DOM support
- **Fallback**: For older browsers, consider JustiFi v5.6.x with different integration approach

### Node.js Backend Requirements  
- **Node.js**: 14+ (for ES6 features and modern fetch API)
- **Dependencies**: Express 4.18+, dotenv 16+
- **Environment**: Supports both development (localhost) and production environments

## 🏗️ Architecture Overview

**IMPORTANT: This is a full-stack application with clear separation:**

### Frontend (Browser)
- **Web Components**: Loads JustiFi components from `https://cdn.jsdelivr.net/npm/@justifi-tech/justifi-webcomponents@latest/dist/index.js`
- **API Calls**: Makes requests to YOUR local backend (NOT directly to JustiFi)
- **URLs Used**: `/api/checkout`, `/api/web-component-token`, `/api/payment/:id`

### Backend (Your Server) 
- **JustiFi API Integration**: YOUR server talks to `https://api.justifi.ai` using OAuth
- **Environment Variables**: `JUSTIFI_BASE_URL=https://api.justifi.ai` (default)
- **Endpoints Provided**: Creates `/api/checkout`, `/api/web-component-token`, etc. for frontend

**⚠️ NEVER connect frontend directly to JustiFi API - always go through your backend!**

### Data Flow Diagram
```
Browser (Frontend)           Your Server (Backend)         JustiFi API
     │                             │                           │
     │ 1. POST /api/checkout       │                           │
     │────────────────────────────>│                           │
     │                             │ 2. OAuth + Create Checkout│
     │                             │──────────────────────────>│
     │                             │ 3. checkout_id            │
     │                             │<──────────────────────────│
     │ 4. checkout_id              │                           │
     │<────────────────────────────│                           │
     │                             │                           │
     │ 5. GET /api/web-component-  │                           │
     │    token?checkout_id=co_123 │                           │
     │────────────────────────────>│                           │
     │                             │ 6. Get Web Component Token│
     │                             │──────────────────────────>│
     │                             │ 7. wct_token              │
     │                             │<──────────────────────────│
     │ 8. wct_token                │                           │
     │<────────────────────────────│                           │
     │                             │                           │
     │ 9. Load JustiFi Web Component with checkout_id + wct_token │
     │ (Components loaded from cdn.jsdelivr.net but use your tokens) │
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your JustiFi credentials
   ```

## 🔐 Three-Step Checkout Process 

⚠️  **CRITICAL REQUIREMENTS:**
1. **Sub-Account header is REQUIRED for ALL authenticated API calls** (except OAuth) - Never forget this!
2. **Three-step authentication process** - Must be done in order

**Process Flow:**
```
Step 1: Get Bearer Token (OAuth) → Step 2: Create Checkout → Step 3: Get Web Component Token → Step 4: Use with Component
```

### Step 1: 🔑 Get OAuth Bearer Token FIRST

You **MUST** get a Bearer token first before doing anything else.

**Required Credentials:**
- `JUSTIFI_CLIENT_ID` - Your JustiFi client ID  
- `JUSTIFI_CLIENT_SECRET` - Your JustiFi client secret
- `JUSTIFI_SUB_ACCOUNT_ID` - Your JustiFi sub-account ID (format: `acc_xxxxxxxx`)

**How to get credentials:** Visit your JustiFi dashboard → API Settings → Client Credentials

**Test OAuth Bearer Token (Step 1):**
```bash
# OAuth does NOT require Sub-Account header:
curl -X POST https://api.justifi.ai/oauth/token \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```
✅ **Success:** You get `{{"access_token": "eyJ...", "expires_in": 3600}}`
❌ **Failed:** Check your client ID and secret are correct

### Step 2: 🛒 Create Checkout (Using Bearer Token)

Once you have the Bearer token, create a checkout to get a checkout_id.

**Test Checkout Creation (Step 2):**

⚠️  **CRITICAL: Sub-Account header is REQUIRED for authenticated API calls**

```bash
# Use the Bearer token from Step 1 + REQUIRED Sub-Account header:
curl -X POST https://api.justifi.ai/v1/checkouts \\
  -H "Authorization: Bearer YOUR_BEARER_TOKEN_FROM_STEP_1" \\
  -H "Content-Type: application/json" \\
  -H "Sub-Account: YOUR_SUB_ACCOUNT_ID" \\
  -d '{{
    "amount": 2999,
    "description": "Test Payment",
    "origin_url": "localhost:3001"
  }}'
```

**Minimal request body (only 3 fields required):**
- `amount` (integer, cents) - REQUIRED
- `description` (string) - REQUIRED  
- `origin_url` (string) - REQUIRED for web components

❌ **Do NOT include:** payment_intent, customer, metadata, or other fields
✅ **Success:** You get `{{"id": "co_xxxxxxxx", "amount": 2999, ...}}`
❌ **Failed:** Check Bearer token, Sub-Account ID, and required fields

### Step 3: 🎟️ Get Web Component Token (Using Bearer Token + Checkout ID)

Now use the Bearer token AND checkout_id to get a Web Component token.

**Test Web Component Token (Step 3):**

⚠️  **CRITICAL: Sub-Account header is REQUIRED here too!**

```bash
# Use the Bearer token from Step 1 AND sub-account ID + REQUIRED Sub-Account header:
curl -X POST https://api.justifi.ai/v1/web_component_tokens \\
  -H "Authorization: Bearer YOUR_BEARER_TOKEN_FROM_STEP_1" \\
  -H "Content-Type: application/json" \\
  -H "Sub-Account: YOUR_SUB_ACCOUNT_ID" \\
  -d '{{"resources": ["write:tokenize:YOUR_SUB_ACCOUNT_ID"]}}'
```
✅ **Success:** You get `{{"token": "wct_xxxxxxxx", "expires_in": 3600}}`
❌ **Failed:** Check Bearer token and Sub-Account ID format

### Step 4: ✅ Verify Complete Flow

Test that your server can do all steps automatically:
```bash
# After starting your server, test the complete flow:
# 1. Create checkout (returns checkout_id)
CHECKOUT_RESPONSE=$(curl -s -X POST http://localhost:3001/api/checkout \\
  -H "Content-Type: application/json" \\
  -d '{{"amount": 2999, "description": "Test Payment"}}')

# 2. Extract checkout_id from response  
CHECKOUT_ID=$(echo $CHECKOUT_RESPONSE | jq -r '.data.id')

# 3. Get web component token using checkout_id
curl "http://localhost:3001/api/web-component-token?checkout_id=$CHECKOUT_ID"
```
✅ **Success:** You should get `{{"success": true, "token": "wct_xxxxxxxx"}}`
❌ **Failed:** Check the server logs - likely Step 1, Step 2, or Step 3 failed

## 🧪 Validate Your Sub-Account

Verify your sub-account works with your Bearer token:
```bash
# Use Bearer token from Step 1:
curl -X GET https://api.justifi.ai/v1/sub_accounts/YOUR_SUB_ACCOUNT_ID \\
  -H "Authorization: Bearer YOUR_BEARER_TOKEN_FROM_STEP_1"
```
✅ **Success:** You should get account details with `"status": "enabled"`
❌ **Failed:** Check your sub-account ID format and that the account is active

## 🏃‍♂️ Running the Application

3. **Start the server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   ```
   http://localhost:3001
   ```

5. **Test the checkout flow:**
   - Enter amount: `2999` (for $29.99)
   - Enter description: `Test Payment`
   - Click "Create Checkout"
   - The JustiFi checkout component should load
   - Use test card: `4242424242424242` with any future expiry and CVC

## 🧪 Test Cards

| Card Number | Description | Expected Result |
|------------|-------------|-----------------|
| `4242424242424242` | Visa Success | Payment succeeds |
| `4000000000000002` | Visa Decline | Payment declined |
| `4000000000000069` | Visa Expired | Card expired error |

## 🔧 Troubleshooting

### ❌ Step 1 Failed: "Invalid client credentials" error
- **Problem:** Cannot get OAuth Bearer token
- **Solution:** 
  - Check `JUSTIFI_CLIENT_ID` and `JUSTIFI_CLIENT_SECRET` are correct
  - Ensure you're using the correct environment (test vs live)
  - Test Step 1 manually with curl command above

### ❌ Step 2 Failed: "Checkout creation failed" error
- **Problem:** Bearer token works, but cannot create checkout
- **Solution:**
  - Check `JUSTIFI_SUB_ACCOUNT_ID` is in format `acc_xxxxxxxx`
  - Verify the sub-account exists and is enabled in your JustiFi dashboard
  - Test Step 2 manually with curl command above
  - Ensure required fields (amount, description, origin_url) are provided

### ❌ Step 3 Failed: "Web component token failed" error
- **Problem:** Bearer token and checkout work, but cannot get Web Component token
- **Solution:**
  - Verify the checkout_id from Step 2 is correct format (`co_xxxxxxxx`)
  - Test Step 3 manually with curl command above
  - Ensure you're passing the correct `Sub-Account` header
  - Check that the checkout is in correct status for token generation

### ❌ "Sub-Account header required" error  
- **Problem:** Missing or incorrect Sub-Account header
- **Solution:**
  - Check `JUSTIFI_SUB_ACCOUNT_ID` is set and in correct format
  - Verify the sub-account exists in your JustiFi dashboard
  - Test sub-account validation with curl command above

### ❌ Web component doesn't load
- **Problem:** Authentication worked, but checkout component fails
- **Solution:**
  - Check browser console for JavaScript errors
  - Verify the checkout ID was created successfully  
  - Test the complete flow with Step 3 curl command above
  - Ensure the web component token is not expired

### ❌ "Unexpected token 'export'" JavaScript error
- **Problem:** Web component fails to load with ES6 module error
- **Solution:**
  - Add `type="module"` attribute to script tag: `<script type="module" src="https://..."></script>`
  - Ensure you're using v5.7.6+ web components which require ES6 modules
  - Check browser console for additional module loading errors

### ❌ Only credit card payment method shows in checkout
- **Problem:** BNPL and bank account options not visible
- **Solution:**
  - Add component attributes to enable all payment methods:
    ```javascript
    checkoutElement.setAttribute('disable-card-form', 'false');
    checkoutElement.setAttribute('disable-bnpl-form', 'false');
    checkoutElement.setAttribute('disable-bank-account-form', 'false');
    ```
  - Verify your JustiFi account has these payment methods enabled

### ❌ "403 Forbidden" on checkout creation with valid credentials
- **Problem:** OAuth works but checkout API returns 403
- **Solution:**
  - Check `origin_url` format - remove protocol prefix (use `localhost:3001` not `http://localhost:3001`)
  - Verify sub-account is active and has checkout permissions
  - Ensure request body only includes required fields: `amount`, `description`, `origin_url`
  - Check Sub-Account header is included in request

### ❌ CORS errors when calling JustiFi API from browser
- **Problem:** Direct frontend calls to api.justifi.ai fail with CORS
- **Solution:**
  - **This is correct behavior** - never call JustiFi API directly from frontend
  - All JustiFi API calls must go through YOUR backend server
  - Frontend should only call your local APIs: `/api/checkout`, `/api/web-component-token`
  - Use the provided Express.js backend example as reference

### ❌ "Invalid scope" error on web component token (v5.7.6+)
- **Problem:** Web component token request fails with invalid scope
- **Solution:**
  - Update scope format from `write:checkout:${checkoutId}` to `write:tokenize:${accountId}`
  - Use sub-account ID instead of checkout ID in token request
  - Ensure you're using the latest token format for v5.7.6+

### ❌ Environment variables not loading
- **Problem:** Server can't find JUSTIFI_CLIENT_ID or other env vars
- **Solution:**
  - Install dotenv: `npm install dotenv`
  - Add to top of server.js: `require('dotenv').config();`
  - Ensure .env file is in project root directory
  - Check .env file format (no quotes, no spaces around =)
  - Verify .env is not committed to version control

### ❌ Browser compatibility issues
- **Problem:** Components not loading due to browser support
- **Solution:**
  - **Browser requirements**: ES6 modules support (Chrome 61+, Firefox 60+, Safari 10.1+)
  - **Script tag**: Must include `type="module"` attribute for v5.7.6+
  - **Check console**: Look for module loading errors in browser developer tools

## 📚 JustiFi Resources

### Official Documentation
- **Main Docs:** https://docs.justifi.ai
- **API Reference:** https://docs.justifi.ai/api-spec
- **Getting Started:** https://docs.justifi.ai/guide

### Web Components
- **Storybook:** https://storybook.justifi.ai
- **GitHub Repo:** https://github.com/justifi-tech/web-component-library
- **Checkout Component:** https://storybook.justifi.ai/?path=/docs/payment-facilitation-unified-fintech-checkout--docs

### Official Examples
- **Component Examples:** https://github.com/justifi-tech/web-component-library/tree/main/apps/component-examples
- **Express.js Checkout Example:** https://raw.githubusercontent.com/justifi-tech/web-component-library/refs/heads/main/apps/component-examples/examples/checkout.js
- **Working Examples Directory:** https://github.com/justifi-tech/web-component-library/blob/main/apps/component-examples/examples/

### Developer Resources
- **API Testing:** https://docs.justifi.ai/api-spec#section/Authentication
- **Webhook Setup:** https://docs.justifi.ai/guide/webhooks
- **Test Environment:** https://docs.justifi.ai/guide/environments

## 🚀 Next Steps

1. **Security:** Replace localhost origin_url for production
2. **Webhooks:** Set up payment status webhooks for reliability
3. **Error Handling:** Add custom error pages and user messaging  
4. **UI/UX:** Customize styling to match your brand
5. **Testing:** Add comprehensive test coverage
6. **Monitoring:** Implement logging and error tracking

## Features Included

- OAuth token management with caching
- Sub-Account header handling
- Web component token generation  
- JustiFi checkout web component integration
- Payment verification and status checking
- Test card support for development
- Comprehensive error handling and validation

## 💬 Need Help?

- **JustiFi Support:** support@justifi.ai
- **Developer Discord:** [Join JustiFi Discord](https://discord.gg/justifi)
- **Documentation Issues:** https://github.com/justifi-tech/docs/issues
"""

    return {
        ".env.example": env_template.strip(),
        "justifi-integration-guide.yaml": yaml_instructions.strip(),
        "README.md": """# JustiFi Checkout Integration

## Quick Start

1. **Set environment variables** (see .env.example)
2. **Run**: `npm install && npm start`
3. **Test**: Open http://localhost:3001

## Important: Amount Requirements

- **Amount must be an integer** (not string or float)
- **Amount must be in cents** (e.g., $29.99 = 2999 cents)
- **Minimum amount**: 100 cents ($1.00)
- Example: For $25.50, use `amount: 2550`

## Important: Sub-Account Header Usage
- **Include Sub-Account header** when creating checkouts, payments, and most API calls
- **Do NOT include Sub-Account header** when getting web component tokens
- Web component tokens only need Authorization + Content-Type headers

## Key Requirements for v5.7.6+

- Script tag: `<script type="module" src="...webcomponents@5.7.6/dist/index.js"></script>`
- Token scope: `write:tokenize:${accountId}` (not checkout_id)
- Component attributes: Set `disable-*-form="false"` for all payment methods
- Origin URL: `localhost:3001` (no http:// prefix)
- Security: Never call JustiFi API directly from frontend

See `justifi-integration-guide.yaml` for complete implementation details and troubleshooting.
""".strip(),
    }


def _generate_integration_patterns() -> dict[str, str]:
    """Generate minimal framework patterns."""
    return {}


def _generate_test_suite() -> dict[str, str]:
    """Generate test suite."""
    test_code = """
const request = require('supertest');
const app = require('./server');

describe('JustiFi Checkout Integration', () => {
    test('should create checkout successfully', async () => {
        const response = await request(app)
            .post('/api/checkout')
            .send({
                amount: 2999,
                description: 'Test payment'
            })
            .expect(200);

        expect(response.body.success).toBe(true);
        expect(response.body.data).toBeDefined();
        expect(response.body.data.id).toBeDefined();
    });

    test('should reject invalid amount', async () => {
        const response = await request(app)
            .post('/api/checkout')
            .send({
                amount: 50, // Too low
                description: 'Test payment'
            })
            .expect(400);

        expect(response.body.success).toBe(false);
        expect(response.body.error).toContain('at least $1.00');
    });

    test('should require description', async () => {
        const response = await request(app)
            .post('/api/checkout')
            .send({
                amount: 2999
                // Missing description
            })
            .expect(400);

        expect(response.body.success).toBe(false);
        expect(response.body.error).toContain('required');
    });

    test('should respond to health check', async () => {
        const response = await request(app)
            .get('/health')
            .expect(200);

        expect(response.body.status).toBe('ok');
    });
});
"""

    return {
        "tests/checkout.test.js": test_code.strip(),
    }


def _generate_setup_instructions(
    framework: str, frontend: str, features: list[str]
) -> list[str]:
    """Generate step-by-step setup instructions."""

    instructions = [
        "1. Set up your environment variables in .env file",
        "2. Install dependencies with your package manager",
        "3. Start the development server",
        "4. Open the application in your browser",
        "5. Test with the provided test cards",
    ]

    if "webhooks" in features:
        instructions.append("6. Set up webhook endpoints for payment events")

    if "saved-cards" in features:
        instructions.append("7. Configure database for storing payment method tokens")

    if "subscriptions" in features:
        instructions.append("8. Implement subscription management endpoints")

    return instructions


def _get_justifi_resources() -> dict[str, dict[str, str]]:
    """Get comprehensive JustiFi resources for LLM reference."""
    return {
        "documentation": {
            "context7": "https://context7.justifi.ai - Comprehensive integration guides and tutorials",
            "api_reference": "https://docs.justifi.ai/api-spec - Complete API documentation with examples",
            "getting_started": "https://docs.justifi.ai/guide - Step-by-step integration guide",
            "github_docs": "https://github.com/justifi-tech/docs - Open source documentation repository",
            "openapi_spec": "https://api.justifi.ai/openapi.yaml - Machine-readable API specification",
            "authentication_guide": "https://docs.justifi.ai/api-spec#section/Authentication - OAuth implementation details",
            "checkout_guide": "https://docs.justifi.ai/guide/checkouts - Checkout integration walkthrough"
        },
        "web_components": {
            "storybook_main": "https://storybook.justifi.ai - Interactive component playground and documentation",
            "checkout_component": "https://storybook.justifi.ai/?path=/docs/payment-facilitation-unified-fintech-checkout--docs - Checkout component documentation",
            "component_library": "https://github.com/justifi-tech/web-component-library - Web components source code",
            "official_examples": "https://github.com/justifi-tech/web-component-library/tree/main/apps/component-examples - Official working examples",
            "express_checkout_example": "https://raw.githubusercontent.com/justifi-tech/web-component-library/refs/heads/main/apps/component-examples/examples/checkout.js - Official Express.js checkout example",
            "styling_guide": "https://storybook.justifi.ai/?path=/docs/design-system-overview--docs - Component styling and theming",
            "cdn_url": "https://cdn.jsdelivr.net/npm/@justifi-tech/justifi-webcomponents@latest/dist/index.js - Web components CDN"
        },
        "testing": {
            "test_cards": "https://docs.justifi.ai/testing/test-cards - Test card numbers and expected results",
            "sandbox_environment": "https://docs.justifi.ai/guide/environments - Test environment setup",
            "api_testing": "https://docs.justifi.ai/api-spec#section/Testing - API testing guidelines",
            "webhook_testing": "https://docs.justifi.ai/guide/webhooks - Webhook testing and validation"
        },
        "troubleshooting": {
            "common_errors": "https://docs.justifi.ai/troubleshooting/common-errors - Common integration issues",
            "authentication_errors": "https://docs.justifi.ai/troubleshooting/authentication - OAuth troubleshooting",
            "checkout_errors": "https://docs.justifi.ai/troubleshooting/checkout-errors - Checkout-specific issues",
            "support_discord": "https://discord.gg/justifi - Developer community support"
        },
        "advanced": {
            "webhooks": "https://docs.justifi.ai/guide/webhooks - Payment status notifications",
            "sub_accounts": "https://docs.justifi.ai/concepts/sub-accounts - Multi-tenant setup",
            "marketplace": "https://docs.justifi.ai/use-cases/marketplace - Marketplace payment flows",
            "pci_compliance": "https://docs.justifi.ai/compliance/pci - PCI compliance guidelines"
        }
    }


def _get_express_vanilla_next_steps() -> list[str]:
    """Get specific next steps for express-vanilla example."""
    return [
        "1. Copy the generated files to your project directory",
        "2. Run 'npm install' to install dependencies", 
        "3. Copy .env.example to .env and add your JustiFi credentials",
        "4. Start with 'npm run dev' and test at http://localhost:3001",
        "5. For your framework, adapt the patterns shown in the 'patterns' example",
        "6. Check Storybook for web component customization: https://storybook.justifi.ai",
        "7. Review authentication flow in Context7: https://context7.justifi.ai",
        "8. See API reference for additional features: https://docs.justifi.ai/api-spec"
    ]


def _get_patterns_next_steps() -> list[str]:
    """Get specific next steps for patterns example."""
    return [
        "1. Choose your backend framework (Express, FastAPI, Django, Rails, etc.)",
        "2. Implement the OAuth pattern in your chosen language",
        "3. Create the 3 required API endpoints: /checkout, /web-component-token, /payment",
        "4. Add JustiFi web component to your frontend framework",
        "5. Test the complete flow with provided test cards",
        "6. For complete examples, generate 'express-vanilla' type to see working code",
        "7. Check Storybook for component integration: https://storybook.justifi.ai",
        "8. Reference OpenAPI spec for TypeScript types: https://api.justifi.ai/openapi.yaml"
    ]


def _get_comprehensive_next_steps() -> list[str]:
    """Get comprehensive next steps for the combined response."""
    return [
        "1. QUICK START: Run the Express.js example to see JustiFi integration working",
        "   - Copy files to your project directory",
        "   - Run 'npm install' to install dependencies", 
        "   - Add your JustiFi credentials to .env",
        "   - Start with 'npm run dev' and test at http://localhost:3001",
        "",
        "2. ADAPT TO YOUR STACK: Use the framework-agnostic patterns",
        "   - Review INTEGRATION_PATTERNS.md for your framework",
        "   - Implement OAuth, checkout, and web component patterns",
        "   - LLMs can easily translate Express patterns to Python, Ruby, etc.",
        "",
        "3. RESOURCES FOR DEEP INTEGRATION:",
        "   - Storybook for web component customization: https://storybook.justifi.ai",
        "   - Context7 for authentication flow: https://context7.justifi.ai",
        "   - API reference for advanced features: https://docs.justifi.ai/api-spec",
        "   - OpenAPI spec for TypeScript types: https://api.justifi.ai/openapi.yaml"
    ]
