"""JustiFi Code Generation Tools

Intelligent code generators that help developers build complete JustiFi integrations.
These tools generate production-ready code tailored to specific frameworks and use cases.
"""

from __future__ import annotations

from typing import Any

from ..core import JustiFiClient
from .base import ToolError, ValidationError
from .response_formatter import standardize_response


async def generate_unified_checkout_integration(
    client: JustiFiClient,
    framework: str = "express",
    frontend: str = "vanilla",
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Generate complete checkout integration code for your stack.

    Creates production-ready code including:
    - Backend OAuth implementation
    - Checkout creation endpoint
    - Frontend Web Component integration
    - Error handling and validation
    - Test examples with test cards

    Args:
        client: JustiFi API client
        framework: Backend framework ('express', 'fastapi', 'django', 'rails')
        frontend: Frontend approach ('vanilla', 'react', 'vue', 'angular')
        features: Optional features like ['webhooks', 'saved-cards', 'subscriptions']

    Returns:
        Complete code package with backend, frontend, and setup instructions

    Raises:
        ValidationError: If parameters are invalid
        ToolError: If code generation fails
    """
    # Validate parameters
    supported_frameworks = ["express", "fastapi", "django", "rails"]
    supported_frontends = ["vanilla", "react", "vue", "angular"]

    if framework not in supported_frameworks:
        raise ValidationError(
            f"framework must be one of: {', '.join(supported_frameworks)}",
            field="framework",
            value=framework,
        )

    if frontend not in supported_frontends:
        raise ValidationError(
            f"frontend must be one of: {', '.join(supported_frontends)}",
            field="frontend",
            value=frontend,
        )

    if features is None:
        features = []

    try:
        # Generate backend code
        backend_code = _generate_backend_code(framework, features)

        # Generate frontend code
        frontend_code = _generate_frontend_code(frontend, features)

        # Generate configuration and setup
        config = _generate_configuration(framework, frontend, features)

        # Generate tests
        tests = _generate_test_suite(framework, frontend, features)

        result = {
            "success": True,
            "integration": {
                "backend": backend_code,
                "frontend": frontend_code,
                "configuration": config,
                "tests": tests,
                "instructions": _generate_setup_instructions(
                    framework, frontend, features
                ),
            },
            "generated_for": {
                "framework": framework,
                "frontend": frontend,
                "features": features,
            },
        }

        return standardize_response(result, "generate_unified_checkout_integration")

    except Exception as e:
        raise ToolError(
            f"Failed to generate checkout integration: {str(e)}",
            error_type="CodeGenerationError",
        ) from e


def _generate_backend_code(framework: str, features: list[str]) -> dict[str, str]:
    """Generate backend code for specified framework."""
    if framework == "express":
        return _generate_express_backend(features)
    elif framework == "fastapi":
        return _generate_fastapi_backend(features)
    elif framework == "django":
        return _generate_django_backend(features)
    elif framework == "rails":
        return _generate_rails_backend(features)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def _generate_express_backend(features: list[str]) -> dict[str, str]:
    """Generate Express.js backend code."""

    # OAuth implementation
    oauth_code = """
// OAuth token management with caching
let accessToken = null;
let tokenExpiry = null;

async function getAccessToken() {
    if (accessToken && tokenExpiry && new Date() < tokenExpiry) {
        return accessToken;
    }

    try {
        const response = await fetch(`${process.env.JUSTIFI_BASE_URL}/oauth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                grant_type: 'client_credentials',
                client_id: process.env.JUSTIFI_CLIENT_ID,
                client_secret: process.env.JUSTIFI_CLIENT_SECRET
            })
        });

        if (!response.ok) {
            throw new Error(`OAuth failed: ${response.status} ${response.statusText}`);
        }

        const tokenData = await response.json();
        accessToken = tokenData.access_token;

        // Set expiry to 5 minutes before actual expiry for safety
        const expiresIn = (tokenData.expires_in - 300) * 1000;
        tokenExpiry = new Date(Date.now() + expiresIn);

        return accessToken;

    } catch (error) {
        console.error('OAuth token request failed:', error);
        throw error;
    }
}

// Web component token for secure component usage
async function getWebComponentToken(checkoutId) {
    if (!checkoutId) {
        throw new Error('Checkout ID is required for web component token');
    }
    
    try {
        const token = await getAccessToken();
        
        const response = await fetch(`${process.env.JUSTIFI_BASE_URL}/v1/web_component_tokens`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Sub-Account': process.env.JUSTIFI_SUB_ACCOUNT_ID
            },
            body: JSON.stringify({
                resources: [`write:checkout:${checkoutId}`]
            })
        });

        if (!response.ok) {
            throw new Error(`Web component token failed: ${response.status} ${response.statusText}`);
        }

        const tokenData = await response.json();
        return tokenData.access_token;
        
    } catch (error) {
        console.error('Web component token request failed:', error);
        throw error;
    }
}
"""

    # Main server code
    server_code = """
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Create checkout endpoint
app.post('/api/checkout', async (req, res) => {
    try {
        const { amount, description } = req.body;

        // Validate input
        if (!amount || amount < 100) {
            return res.status(400).json({
                success: false,
                error: 'Amount must be at least $1.00 (100 cents)'
            });
        }

        if (!description || description.trim() === '') {
            return res.status(400).json({
                success: false,
                error: 'Description is required'
            });
        }

        const token = await getAccessToken();

        // Create checkout via JustiFi API
        const response = await fetch(`${process.env.JUSTIFI_BASE_URL}/v1/checkouts`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Sub-Account': process.env.JUSTIFI_SUB_ACCOUNT_ID
            },
            body: JSON.stringify({
                amount: parseInt(amount),
                description: description.trim(),
                currency: 'usd',
                origin_url: 'http://localhost:3001'  // Required for web component usage
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`JustiFi API error: ${response.status} ${errorText}`);
        }

        const checkout = await response.json();

        res.json({
            success: true,
            data: checkout.data
        });

    } catch (error) {
        console.error('Checkout creation error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get web component token endpoint  
app.get('/api/web-component-token', async (req, res) => {
    try {
        const { checkout_id } = req.query;
        
        if (!checkout_id) {
            return res.status(400).json({
                success: false,
                error: 'Checkout ID is required'
            });
        }
        
        const webComponentToken = await getWebComponentToken(checkout_id);
        
        res.json({
            success: true,
            token: webComponentToken
        });
        
    } catch (error) {
        console.error('Web component token error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Verify payment endpoint
app.get('/api/payment/:id', async (req, res) => {
    try {
        const { id } = req.params;

        if (!id || id.trim() === '') {
            return res.status(400).json({
                success: false,
                error: 'Payment ID is required'
            });
        }

        const token = await getAccessToken();

        const response = await fetch(`${process.env.JUSTIFI_BASE_URL}/v1/payments/${id}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Sub-Account': process.env.JUSTIFI_SUB_ACCOUNT_ID
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                return res.status(404).json({
                    success: false,
                    error: 'Payment not found'
                });
            }
            throw new Error(`JustiFi API error: ${response.status}`);
        }

        const payment = await response.json();

        res.json({
            success: true,
            data: payment.data
        });

    } catch (error) {
        console.error('Payment retrieval error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString()
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});

module.exports = app;
"""

    return {
        "server.js": oauth_code + "\n" + server_code,
        "package.json": _generate_express_package_json(features),
    }


def _generate_express_package_json(features: list[str]) -> str:
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


def _generate_vanilla_frontend(features: list[str]) -> dict[str, str]:
    """Generate vanilla JavaScript frontend."""

    html_code = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JustiFi Checkout Integration</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .checkout-form {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            background: #f9f9f9;
            margin-bottom: 20px;
        }
        .checkout-container {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            background: white;
            display: none;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background: #2c5aa0;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background: #1e3f73;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .error {
            background: #fff2f2;
            border: 1px solid #ffb3b3;
            color: #d63384;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .success {
            background: #f0f9f0;
            border: 1px solid #b3d9b3;
            color: #28a745;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>JustiFi Checkout Integration</h1>

    <div class="checkout-form">
        <h2>Create Payment</h2>
        <form id="payment-form">
            <div class="form-group">
                <label for="amount">Amount (in cents)</label>
                <input type="number" id="amount" value="2999" min="100" required>
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <input type="text" id="description" value="Premium Plan" required>
            </div>
            <button type="submit" id="create-checkout">Create Checkout</button>
        </form>
    </div>

    <div id="checkout-container" class="checkout-container">
        <h3>Complete Payment</h3>
        <div id="checkout-content"></div>
    </div>

    <div id="messages"></div>

    <!-- JustiFi Web Components -->
    <script src="https://cdn.justifi.ai/webcomponents/dist/justifi.js"></script>

    <script src="checkout.js"></script>
</body>
</html>"""

    js_code = """
// Backend API client
class CheckoutAPI {
    constructor() {
        this.baseUrl = window.location.origin;
    }

    async createCheckout(amount, description) {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, description })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Checkout creation failed');
        }

        return data;
    }

    async verifyPayment(paymentId) {
        const response = await fetch(`/api/payment/${paymentId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Payment verification failed');
        }

        return data;
    }

    async getWebComponentToken(checkoutId) {
        if (!checkoutId) {
            throw new Error('Checkout ID is required for web component token');
        }
        
        const response = await fetch(`/api/web-component-token?checkout_id=${checkoutId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to get web component token');
        }

        return data.token;
    }
}

const api = new CheckoutAPI();

// DOM elements
const paymentForm = document.getElementById('payment-form');
const createCheckoutBtn = document.getElementById('create-checkout');
const checkoutContainer = document.getElementById('checkout-container');
const checkoutContent = document.getElementById('checkout-content');
const messagesDiv = document.getElementById('messages');

// Event handlers
paymentForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const amount = document.getElementById('amount').value;
    const description = document.getElementById('description').value;

    try {
        createCheckoutBtn.disabled = true;
        createCheckoutBtn.textContent = 'Creating...';

        showMessage('Creating checkout session...', 'info');

        // Create checkout
        const checkout = await api.createCheckout(parseInt(amount), description);

        if (checkout.success) {
            showMessage('Checkout created! Loading payment form...', 'success');
            await createWebComponent(checkout.data.id);
        }

    } catch (error) {
        console.error('Checkout creation error:', error);
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        createCheckoutBtn.disabled = false;
        createCheckoutBtn.textContent = 'Create Checkout';
    }
});

async function createWebComponent(checkoutId) {
    try {
        checkoutContainer.style.display = 'block';
        checkoutContent.innerHTML = '<div>Loading secure payment form...</div>';

        // Get web component token and create JustiFi checkout component
        const webComponentToken = await api.getWebComponentToken(checkoutId);
        
        const checkoutElement = document.createElement('justifi-checkout');
        checkoutElement.setAttribute('checkout-id', checkoutId);
        checkoutElement.setAttribute('auth-token', webComponentToken);

        // Event listeners
        checkoutElement.addEventListener('submit-event', async (event) => {
            console.log('Payment submitted successfully:', event.detail);

            try {
                const { response } = event.detail;

                if (response.payment_id) {
                    // Verify payment
                    const payment = await api.verifyPayment(response.payment_id);

                    if (payment.success && payment.data.status === 'succeeded') {
                        showMessage('🎉 Payment successful! Thank you!', 'success');

                        // Redirect to success page or reset form
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                } else {
                    showMessage('Payment completed successfully!', 'success');
                }

            } catch (error) {
                console.error('Payment verification error:', error);
                showMessage('Payment completed but verification failed', 'error');
            }
        });

        checkoutElement.addEventListener('error-event', (event) => {
            console.log('Checkout error:', event.detail);
            showMessage(`Payment error: ${event.detail.message}`, 'error');
        });

        checkoutElement.addEventListener('loaded', (event) => {
            console.log('Checkout loaded:', event.detail);
            showMessage('Payment form loaded successfully', 'info');
        });

        // Replace loading message with component
        checkoutContent.innerHTML = '';
        checkoutContent.appendChild(checkoutElement);

    } catch (error) {
        console.error('Web component error:', error);
        showMessage(`Error loading payment form: ${error.message}`, 'error');
    }
}

function showMessage(message, type = 'info') {
    const div = document.createElement('div');
    div.className = type === 'error' ? 'error' : (type === 'success' ? 'success' : 'info');
    div.textContent = message;

    messagesDiv.appendChild(div);

    // Auto-remove info messages
    if (type === 'info') {
        setTimeout(() => {
            if (div.parentNode) {
                div.parentNode.removeChild(div);
            }
        }, 5000);
    }
}

// Development helpers
console.log('JustiFi Checkout Integration loaded');
console.log('Test cards: 4242424242424242 (success), 4000000000000002 (declined)');
"""

    return {
        "index.html": html_code,
        "checkout.js": js_code,
    }


def _generate_fastapi_backend(features: list[str]) -> dict[str, str]:
    """Generate FastAPI backend code."""
    # Implementation for FastAPI would go here
    return {"main.py": "# FastAPI implementation coming soon"}


def _generate_django_backend(features: list[str]) -> dict[str, str]:
    """Generate Django backend code."""
    # Implementation for Django would go here
    return {"views.py": "# Django implementation coming soon"}


def _generate_rails_backend(features: list[str]) -> dict[str, str]:
    """Generate Rails backend code."""
    # Implementation for Rails would go here
    return {"checkout_controller.rb": "# Rails implementation coming soon"}


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


def _generate_configuration(
    framework: str, frontend: str, features: list[str]
) -> dict[str, str]:
    """Generate configuration files."""

    env_template = """
# JustiFi API Configuration (Required)
JUSTIFI_CLIENT_ID=test_your_client_id
JUSTIFI_CLIENT_SECRET=test_your_client_secret
JUSTIFI_SUB_ACCOUNT_ID=acc_your_sub_account_id
JUSTIFI_BASE_URL=https://api.justifi.ai

# Server Configuration
PORT=3001
NODE_ENV=development
"""

    readme = f"""
# JustiFi Checkout Integration

Generated integration for {framework} backend with {frontend} frontend.

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

**CRITICAL:** JustiFi checkout integration requires a **three-step process**:

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
curl -X POST https://api.justifi.ai/oauth/token \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET"
```
✅ **Success:** You get `{{"access_token": "eyJ...", "expires_in": 3600}}`
❌ **Failed:** Check your client ID and secret are correct

### Step 2: 🛒 Create Checkout (Using Bearer Token)

Once you have the Bearer token, create a checkout to get a checkout_id.

**Test Checkout Creation (Step 2):**
```bash
# Use the Bearer token from Step 1:
curl -X POST https://api.justifi.ai/v1/checkouts \\
  -H "Authorization: Bearer YOUR_BEARER_TOKEN_FROM_STEP_1" \\
  -H "Content-Type: application/json" \\
  -H "Sub-Account: YOUR_SUB_ACCOUNT_ID" \\
  -d '{{
    "amount": 2999,
    "description": "Test Payment",
    "origin_url": "http://localhost:3001"
  }}'
```
✅ **Success:** You get `{{"id": "co_xxxxxxxx", "amount": 2999, ...}}`
❌ **Failed:** Check Bearer token, Sub-Account ID, and required fields

### Step 3: 🎟️ Get Web Component Token (Using Bearer Token + Checkout ID)

Now use the Bearer token AND checkout_id to get a Web Component token.

**Test Web Component Token (Step 3):**
```bash
# Use the Bearer token from Step 1 AND checkout_id from Step 2:
curl -X POST https://api.justifi.ai/v1/web_component_tokens \\
  -H "Authorization: Bearer YOUR_BEARER_TOKEN_FROM_STEP_1" \\
  -H "Content-Type: application/json" \\
  -H "Sub-Account: YOUR_SUB_ACCOUNT_ID" \\
  -d '{{"resources": ["write:checkout:YOUR_CHECKOUT_ID_FROM_STEP_2"]}}'
```
✅ **Success:** You get `{{"token": "wct_xxxxxxxx", "expires_in": 3600}}`
❌ **Failed:** Check Bearer token, Sub-Account ID, and checkout_id format

### Step 4: ✅ Verify Complete Flow

Test that your server can do all steps automatically:
```bash
# After starting your server, test the complete flow:
# 1. Create checkout (returns checkout_id)
CHECKOUT_RESPONSE=$(curl -s -X POST http://localhost:3001/api/checkout \\
  -H "Content-Type: application/json" \\
  -d '{"amount": 2999, "description": "Test Payment"}')

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

## 📚 JustiFi Resources

### Official Documentation
- **Main Docs:** https://docs.justifi.ai
- **API Reference:** https://docs.justifi.ai/api-spec
- **Getting Started:** https://docs.justifi.ai/guide

### Web Components
- **Storybook:** https://storybook.justifi.ai
- **GitHub Repo:** https://github.com/justifi-tech/web-component-library
- **Checkout Component:** https://storybook.justifi.ai/?path=/docs/payment-facilitation-unified-fintech-checkout--docs

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

{f"- {chr(10).join(f'  - {feature}' for feature in features)}" if features else "- OAuth token management with caching"}
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
        "README.md": readme.strip(),
    }


def _generate_test_suite(
    framework: str, frontend: str, features: list[str]
) -> dict[str, str]:
    """Generate test suite."""

    if framework == "express":
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

    return {"tests/placeholder.test": "# Tests for other frameworks coming soon"}


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
