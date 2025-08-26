# Embedded Checkout Example

This example demonstrates how to build a real-world checkout flow using the JustiFi API. The MCP server assists developers in their IDE by helping them understand the API and generate the backend code, but the final implementation makes actual API calls to JustiFi.

## Development Workflow

1. **IDE Integration**: Use MCP server in Cursor/Claude Code to explore JustiFi API capabilities
2. **Backend Development**: Build real Express.js server that calls JustiFi API directly  
3. **Frontend Integration**: JustiFi Web Components communicate with your real backend
4. **Production Ready**: Final code makes actual API calls, not MCP calls

## Prerequisites

- JustiFi test API credentials
- MCP server running locally
- Modern web browser

## Setup

1. Configure your environment variables:
```bash
export JUSTIFI_CLIENT_ID="test_your_client_id"
export JUSTIFI_CLIENT_SECRET="test_your_client_secret"
export JUSTIFI_BASE_URL="https://api.justifi.ai"  # or staging URL
```

2. Start the MCP server:
```bash
cd ../../..
make dev
```

3. Open `index.html` in your browser or serve it locally:
```bash
python -m http.server 8000
# Then visit http://localhost:8000
```

## How It Works

### 1. MCP-Assisted Development
Developers use the MCP server in their IDE to:
- Explore JustiFi API endpoints and parameters
- Generate backend code with proper authentication
- Understand payment flow requirements and security practices

### 2. Real Backend Implementation
The Express.js server makes actual HTTP calls to JustiFi API:
```javascript
// Real API call to JustiFi (not MCP simulation)
app.post('/api/checkout', async (req, res) => {
  const response = await fetch('https://api.justifi.ai/v1/checkouts', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      amount: req.body.amount,
      description: req.body.description
    })
  });
  
  const checkout = await response.json();
  res.json(checkout);
});
```

### 3. Frontend Integration
The frontend calls your real backend, which then calls JustiFi:
```javascript
// Frontend calls your backend (not MCP)
const response = await fetch('/api/checkout', {
  method: 'POST',
  body: JSON.stringify({
    amount: 2999,
    description: 'Premium Plan'
  })
});

const checkout = await response.json();
```

### 4. Web Component Integration
JustiFi Checkout Web Component integration:
```javascript
const element = document.createElement('justifi-checkout');
element.setAttribute('checkout-id', checkout.data.id);
element.setAttribute('auth-token', 'your_auth_token');

// Optional: Customize payment methods
element.setAttribute('disable-bnpl', 'false');
element.setAttribute('disable-credit-card', 'false');

// Handle real events
element.addEventListener('submit-event', (e) => {
  console.log('Payment completed:', e.detail.response);
});

element.addEventListener('error-event', (e) => {
  console.error('Error:', e.detail.message);
});

element.addEventListener('loaded', (e) => {
  console.log('Checkout loaded:', e.detail.checkout_status);
});
```

## Test Cards

Use these test card numbers for testing:
- **4242424242424242** - Visa (success)
- **4000000000000002** - Visa (declined)
- **4000000000000341** - Visa (fails after tokenization)

Expiration: Any future date  
CVC: Any 3-digit number

## Security Features

- All checkout creation uses test credentials only
- No sensitive card data stored locally
- PCI-compliant payment processing through JustiFi
- Secure tokenization before payment creation

## Troubleshooting

**Checkout creation fails**: Ensure you're using test credentials and the MCP server is running.

**Web Component not loading**: Check that you have internet connectivity and the JustiFi CDN is accessible.

**Payment events not firing**: Make sure you're listening for events before creating the checkout.