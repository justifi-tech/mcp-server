# JustiFi Web Components Specifications

This document contains the **authoritative specifications** for JustiFi Web Components, based on the actual component source code from the web-component-library repository.

## Core Components

### justifi-checkout

**Purpose**: Complete checkout flow with secure payment processing

**HTML Tag**: `<justifi-checkout></justifi-checkout>`

**Required Attributes**:
- `checkout-id`: The ID of the checkout session created via JustiFi API
- `auth-token`: Authentication token for the checkout session

**Events**:
- `submit-event`: Fired when payment is successfully submitted
  - `event.detail.response.payment_id`: ID of the created payment
  - `event.detail.response.payment_method_id`: ID of the payment method used
  - `event.detail.response.status`: Payment status
- `error-event`: Fired when an error occurs
  - `event.detail.message`: Error message
  - `event.detail.errorCode`: Error code
  - `event.detail.severity`: Error severity level
- `loaded`: Fired when the checkout component is fully loaded
  - `event.detail.checkout_status`: Current status of the checkout

**Example Usage**:
```javascript
const checkoutElement = document.createElement('justifi-checkout');
checkoutElement.setAttribute('checkout-id', 'chkt_123456789');
checkoutElement.setAttribute('auth-token', 'your_auth_token');

checkoutElement.addEventListener('submit-event', async (event) => {
  const { response } = event.detail;
  console.log('Payment completed:', response.payment_id);
});

checkoutElement.addEventListener('error-event', (event) => {
  console.error('Checkout error:', event.detail.message);
});

checkoutElement.addEventListener('loaded', (event) => {
  console.log('Checkout loaded:', event.detail.checkout_status);
});

document.body.appendChild(checkoutElement);
```

### justifi-card-form

**Purpose**: Secure card capture form for tokenization

**HTML Tag**: `<justifi-card-form></justifi-card-form>`

**Attributes**:
- `iframe-origin`: URL for the rendered iFrame (advanced usage)
- `single-line`: Boolean indicating if the Card Form should render in a single line
- `validation-mode`: When to trigger validation ("all", "onBlur", "onChange", "onSubmit", "onTouched")
- `style-overrides`: Stringified Theme object for custom styling

**Events**:
- `cardFormReady`: Fired when iframe has loaded and form is ready
- `cardFormTokenize`: Fired when tokenize method is called
  - `event.detail.data`: Tokenization result object
- `cardFormValidate`: Fired when validate method is called
  - `event.detail.data.isValid`: Boolean indicating if form is valid
- `ready`: Alternative ready event (deprecated, use cardFormReady)

**Methods**:
- `tokenize(clientId, paymentMethodMetadata, account?)`: Creates a payment method token
  - Returns: `Promise<CreatePaymentMethodResponse>`
- `validate()`: Validates the form
  - Returns: `Promise<{ isValid: boolean }>`

**Example Usage**:
```javascript
const cardForm = document.createElement('justifi-card-form');

cardForm.addEventListener('cardFormReady', () => {
  console.log('Card form is ready for input');
});

cardForm.addEventListener('cardFormTokenize', (event) => {
  const tokenData = event.detail.data;
  console.log('Tokenization completed:', tokenData.id);
  
  // Store the token securely in your backend
  fetch('/api/payment-methods', {
    method: 'POST',
    body: JSON.stringify({ token: tokenData.id })
  });
});

document.body.appendChild(cardForm);

// To tokenize a payment method
const paymentMethodData = {
  name: 'John Doe',
  address_line1: '123 Broadway',
  address_city: 'Minneapolis',
  address_state: 'MN',
  address_postal_code: '55413',
  address_country: 'US'
};

cardForm.tokenize('your_client_id', paymentMethodData, 'optional_account_id');
```

## CDN Integration

Use the official CDN for loading components:

**ESM (Modern browsers)**:
```html
<script type="module" src="https://cdn.jsdelivr.net/npm/@justifi/webcomponents@latest/dist/webcomponents/webcomponents.esm.js"></script>
```

**UMD (Legacy browsers)**:
```html
<script nomodule src="https://cdn.jsdelivr.net/npm/@justifi/webcomponents@latest/dist/webcomponents/webcomponents.js"></script>
```

**Alternative CDN (internal)**:
```html
<script src="https://cdn.justifi.ai/webcomponents/dist/justifi.js"></script>
```

## Security Best Practices

1. **Never expose live credentials in frontend code**: Use environment-appropriate tokens
2. **Tokenization-only mode**: Components handle PCI-compliant card data capture
3. **Event-driven architecture**: Listen to component events rather than polling
4. **Server-side verification**: Always verify payment results on your backend

## Development vs Production

- **Development**: Use test credentials and staging API endpoints
- **Production**: Use live credentials with proper token management
- **MCP Integration**: Use MCP server in IDE for API exploration and code generation, not in production

## Common Patterns

### Checkout Flow
1. Create checkout session via JustiFi API (backend)
2. Pass checkout ID to `justifi-checkout` component (frontend)
3. Handle `submit-event` for successful payments (frontend)
4. Verify payment status via API (backend)

### Tokenization Flow
1. Capture card details with `justifi-card-form` (frontend)
2. Handle `cardFormTokenize` event with token data (frontend)
3. Store token securely via API (backend)
4. Use stored token for future payments (backend)

---

**Last Updated**: Based on actual component source code from web-component-library repository
**Version**: Components v2.1.0+