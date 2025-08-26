# JustiFi Web Components Examples

This directory contains complete examples showing how to integrate JustiFi MCP tools with JustiFi Web Components for secure, PCI-compliant payment solutions.

## Quick Start

1. **Start the MCP server**:
   ```bash
   cd ../..
   make dev
   ```

2. **Configure your credentials**:
   ```bash
   export JUSTIFI_CLIENT_ID="test_your_client_id"
   export JUSTIFI_CLIENT_SECRET="test_your_client_secret"
   export JUSTIFI_BASE_URL="https://api.justifi.ai"
   ```

3. **Serve the examples**:
   ```bash
   cd examples/web-components
   python -m http.server 8000
   ```

4. **Open in browser**: http://localhost:8000

## Examples

### 🛒 [Embedded Checkout](./embedded-checkout/)
Complete checkout flow with hosted payment form.

**Features:**
- MCP creates checkout session
- Web Component renders secure payment form
- Handles payment completion events
- Error handling and retry logic

**Best for:** Simple checkout flows, quick prototyping

### 🔐 [Tokenization Flow](./tokenization/)
Secure card tokenization for saved payment methods.

**Features:**
- Web Component captures card details securely
- MCP tokenizes payment method
- Store and reuse payment methods
- PCI-compliant card handling

**Best for:** Subscription services, returning customers

### 📊 [Payment Dashboard](./dashboard/)
Analytics dashboard with real-time payment data.

**Features:**
- Fetch transaction data via MCP tools
- Display in interactive dashboard
- Real-time updates and search
- Analytics visualization with charts

**Best for:** Admin dashboards, reporting tools

## Architecture

The MCP server acts as your **IDE development assistant**, helping you build real applications that call the JustiFi API directly.

**Development Phase (MCP-Assisted):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Developer IDE   │    │   MCP Server    │    │  JustiFi API    │
│ (Cursor/Claude) │◄──►│  (Assistant)    │◄──►│ (Reference)     │
│                 │    │                 │    │                 │
│ • Code Gen      │    │ • API Discovery │    │ • Documentation │
│ • Understanding │    │ • Best Practices│    │ • Validation    │
│ • Prototyping   │    │ • Error Guidance│    │ • Test Data     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Production Application (Generated Code):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Your Backend  │    │  JustiFi API    │
│ Web Components  │◄──►│ (Real Server)   │◄──►│ (Live Calls)    │
│                 │    │                 │    │                 │
│ • Card Forms    │    │ • OAuth/Auth    │    │ • Secure        │
│ • Checkout UI   │    │ • HTTP Requests │    │   Processing    │
│ • Payment Status│    │ • Data Handling │    │ • Compliance    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Testing

Run the included test suite to validate examples:

```bash
node test-runner.js
```

The test runner will:
- ✅ Validate file structure
- ✅ Check HTML content and JavaScript
- ✅ Verify MCP integration points
- ✅ Confirm Web Component usage
- ✅ Test security features

## Test Cards

All examples support these test card numbers:

| Card Number | Brand | Result |
|------------|-------|---------|
| 4242424242424242 | Visa | Success |
| 4000000000000002 | Visa | Declined |
| 4000000000000341 | Visa | Fails after tokenization |
| 5555555555554444 | Mastercard | Success |
| 378282246310005 | Amex | Success |

**Expiration:** Any future date  
**CVC:** Any 3-digit number

## Security Features

- 🔒 **PCI Compliance**: Web Components handle sensitive data
- 🧪 **Test Mode Only**: MCP enforces test credentials
- 🛡️ **No Raw Card Storage**: Immediate tokenization
- 🔐 **Environment Detection**: Automatic test/prod validation

## Common Integration Patterns

### 1. Create → Render → Handle
```javascript
// 1. Backend: Create via MCP
const checkout = await mcp.tools.create_checkout(params);

// 2. Frontend: Render Web Component  
const element = document.createElement('justifi-checkout');
element.setAttribute('checkout-id', checkout.data.id);

// 3. Handle events
element.addEventListener('payment-complete', handleSuccess);
```

### 2. Capture → Tokenize → Store
```javascript
// 1. Frontend: Capture card
cardForm.addEventListener('card-submitted', async (event) => {
  // 2. Backend: Tokenize via MCP
  const token = await mcp.tools.tokenize_payment_method(event.detail);
  // 3. Store token (not card data)
  await savePaymentMethod(token.data.id);
});
```

### 3. Fetch → Display → Interact
```javascript
// 1. Backend: Fetch data via MCP
const payments = await mcp.tools.list_payments();
// 2. Frontend: Display in components
renderPaymentsList(payments.data);
// 3. Handle interactions
handlePaymentActions();
```

## Customization

All examples are designed to be easily customizable:

- **Styling**: Modify CSS variables and classes
- **Business Logic**: Add your own validation and workflows  
- **Data Sources**: Connect to your database and APIs
- **UI Components**: Replace with your preferred libraries

## Production Deployment

Before going live:

1. **Replace test credentials** with live API keys
2. **Add proper authentication** and user management
3. **Implement webhooks** for real-time updates
4. **Add monitoring** and error tracking
5. **Configure CSP headers** for security
6. **Set up SSL/TLS** encryption

## Documentation

- 📚 [Web Components Integration Guide](../../docs/WEB_COMPONENTS_INTEGRATION.md)
- 🔧 [MCP Server Documentation](../../README.md)
- 🌐 [JustiFi API Reference](https://docs.justifi.ai/)

## Support

- 🐛 [Report Issues](https://github.com/justifi-tech/mcp-server/issues)
- 💬 [Join Discord](https://discord.gg/justifi)
- 📧 [Contact Support](mailto:support@justifi.ai)

---

*These examples demonstrate secure payment integration patterns. Always follow PCI compliance guidelines when handling payment data.*