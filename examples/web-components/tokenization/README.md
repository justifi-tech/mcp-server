# Tokenization Flow Example

This example demonstrates building a real-world tokenization flow using the JustiFi API. The MCP server assists developers in their IDE by helping them understand tokenization requirements and generate secure backend code.

## Development Workflow

1. **IDE Integration**: Use MCP server in Cursor/Claude Code to understand tokenization API endpoints
2. **Backend Development**: Build secure tokenization endpoints that call JustiFi API directly
3. **Frontend Integration**: JustiFi Web Components capture cards, backend handles tokenization
4. **Token Management**: Store and reuse tokens for future payments (PCI-compliant)

## Prerequisites

- JustiFi test API credentials
- MCP server running locally
- Modern web browser

## Setup

1. Configure your environment variables:
```bash
export JUSTIFI_CLIENT_ID="test_your_client_id"
export JUSTIFI_CLIENT_SECRET="test_your_client_secret"
export JUSTIFI_BASE_URL="https://api.justifi.ai"
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

### 1. Card Capture (Web Components)
The JustiFi card form securely captures card details without your server touching sensitive data:
```javascript
const cardElement = document.createElement('justifi-card-form');
cardElement.setAttribute('tokenization-only', 'true');
```

### 2. Real Backend Tokenization
Your backend makes actual JustiFi API calls (learned via MCP during development):
```javascript
// Backend endpoint for tokenization
app.post('/api/tokenize', async (req, res) => {
  const response = await fetch('https://api.justifi.ai/v1/payment_methods', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      type: 'card',
      card: {
        number: req.body.card_number,
        exp_month: req.body.exp_month,
        exp_year: req.body.exp_year,
        cvc: req.body.cvc
      }
    })
  });
  
  const token = await response.json();
  res.json(token);
});
```

### 3. Frontend Integration
Frontend calls your real backend for tokenization:
```javascript
// Frontend calls your backend (not MCP)
const response = await fetch('/api/tokenize', {
  method: 'POST',
  body: JSON.stringify({
    card_number: cardData.number,
    exp_month: cardData.exp_month,
    exp_year: cardData.exp_year,
    cvc: cardData.cvc
  })
});

const token = await response.json();
```

### 4. Payment Creation
Use tokens for payments via your real backend:
```javascript
const payment = await fetch('/api/payments', {
  method: 'POST',
  body: JSON.stringify({
    amount: 1999,
    payment_method_id: token.id,
    description: 'Subscription payment'
  })
});
```

## Security Features

- **No raw card storage**: Cards are tokenized immediately
- **PCI compliance**: JustiFi handles all sensitive data
- **Test mode only**: MCP enforces test credentials for payment creation
- **Token reuse**: Safely store and reuse payment methods

## Test Cards

Use these test card numbers:
- **4242424242424242** - Visa (success)
- **4000000000000002** - Visa (declined)
- **4000000000000341** - Visa (fails after tokenization)

## Use Cases

- **Subscription services**: Store customer payment methods securely
- **E-commerce**: Save cards for faster checkout
- **Marketplace platforms**: Multiple payment methods per customer
- **Recurring billing**: Automated payments with stored methods

## Flow Diagram

```
1. Customer enters card details
   ↓
2. Web Component validates format
   ↓  
3. MCP tokenizes card → Token ID
   ↓
4. Store token ID (not card data)
   ↓
5. Use token for payments
```

## Troubleshooting

**Tokenization fails**: Ensure test cards and test credentials are being used.

**Token not found**: Tokens are tied to the client_id that created them.

**Payment fails**: Check that the token is valid and hasn't been deleted.