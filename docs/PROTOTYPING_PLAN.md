# JustiFi MCP Server - Prototyping Excellence Plan
**INTERNAL PLANNING DOCUMENT - DO NOT COMMIT**

## Vision
Transform the JustiFi MCP Server into the premier tool for developers using Cursor or Claude Code to rapidly prototype payment solutions with JustiFi's API and Web Components.

## Current State Assessment
- ✅ 36 read-only tools for payment data retrieval
- ✅ Comprehensive coverage of payment domains
- ✅ Basic JUSTIFI_BASE_URL support exists
- ❌ No payment creation capabilities
- ❌ No Web Component integration examples
- ❌ Limited prototyping guidance
- ❌ Base URL configuration not well documented

## Master Roadmap

### Phase 0: Enhanced Configuration Support (Week 1)
**Goal**: Robust base URL configuration for staging, local dev, and proxies

### Phase 1: Secure Payment Creation Tools (Weeks 1-2) 
**Goal**: PCI-compliant payment creation with test-mode enforcement

### Phase 2: Web Component Integration (Weeks 3-4)
**Goal**: Seamless MCP + Web Component examples

### Phase 3: Developer Experience Enhancement (Weeks 5-6)
**Goal**: Templates and intelligent prototyping assistance

### Phase 4: Advanced Prototyping Features (Weeks 7-8)
**Goal**: Testing utilities, webhooks, production patterns

---

## Phase 0: Enhanced Configuration Support (PREREQUISITE)

### Objective
Enable flexible environment configuration for staging, local development, and proxy setups.

### Current State
- `JUSTIFI_BASE_URL` is read from environment in `python/core.py`
- Default is `https://api.justifi.ai`
- Not well documented or exposed in all contexts

### Required Changes

#### 1. Configuration Enhancement
```python
# python/core.py - Enhanced initialization
class JustiFiClient:
    def __init__(self, client_id: str, client_secret: str, base_url: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Priority: explicit parameter > env var > default
        self.base_url = base_url or os.getenv("JUSTIFI_BASE_URL", "https://api.justifi.ai")
        
        # Normalize URL
        self.base_url = self.base_url.rstrip('/')
        if '/v1' in self.base_url:
            logger.warning(f"Base URL should not include /v1 suffix: {self.base_url}")
            self.base_url = self.base_url.replace('/v1', '')
        
        # Log configuration for debugging
        logger.info(f"JustiFi client initialized:")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Client ID prefix: {client_id[:8]}...")
        logger.info(f"  Environment: {'test' if client_id.startswith('test_') else 'live'}")
```

#### 2. Configuration Documentation Updates

**README.md additions:**
```markdown
### Environment Configuration

#### Base URL Configuration
The MCP server supports custom base URLs for different environments:

```bash
# Production (default)
JUSTIFI_BASE_URL=https://api.justifi.ai

# Staging environment
JUSTIFI_BASE_URL=https://staging.api.justifi.ai

# Local development
JUSTIFI_BASE_URL=http://localhost:3000

# Corporate proxy
JUSTIFI_BASE_URL=https://proxy.company.com/justifi
```

#### Configuration Methods

1. **Environment Variables** (Recommended)
   ```bash
   export JUSTIFI_BASE_URL=https://staging.api.justifi.ai
   export JUSTIFI_CLIENT_ID=test_abc123
   export JUSTIFI_CLIENT_SECRET=test_secret456
   ```

2. **MCP Configuration Files**
   ```json
   {
     "mcpServers": {
       "justifi": {
         "command": "npx",
         "args": ["@justifi/mcp-server"],
         "env": {
           "JUSTIFI_CLIENT_ID": "test_...",
           "JUSTIFI_CLIENT_SECRET": "test_...",
           "JUSTIFI_BASE_URL": "https://staging.api.justifi.ai"
         }
       }
     }
   }
   ```
```

#### 3. Environment Detection Logic
```python
# python/tools/utils/environment.py
def detect_environment(base_url: str, client_id: str) -> dict:
    """Detect and validate environment configuration"""
    
    env_info = {
        'is_production': 'api.justifi.ai' in base_url and '/staging' not in base_url,
        'is_staging': 'staging' in base_url,
        'is_local': 'localhost' in base_url or '127.0.0.1' in base_url,
        'is_proxy': 'proxy' in base_url,
        'is_test_key': client_id.startswith('test_'),
        'is_live_key': client_id.startswith('live_'),
    }
    
    # Validate configuration
    if env_info['is_production'] and env_info['is_live_key']:
        logger.warning("Using LIVE keys in PRODUCTION environment")
    
    return env_info
```

---

## Phase 1: Secure Payment Creation Tools

### Objective
Enable payment creation while maintaining PCI compliance through test-mode enforcement.

### Core Principle
**Most operations work in both test and production, but payment CREATION is restricted to test mode only.**

### Security Architecture

#### Test Card Validation
```python
# python/tools/utils/test_cards.py

JUSTIFI_TEST_CARDS = {
    # Successful test cards
    '4242424242424242',  # Visa
    '4000056655665556',  # Visa debit
    '5555555555554444',  # Mastercard
    '2223003122003222',  # Mastercard 2-series
    '5200828282828210',  # Mastercard debit
    '5105105105105100',  # Mastercard prepaid
    '378282246310005',   # American Express
    '371449635398431',   # American Express
    '6011000990139424',  # Discover
    '3056930009020004',  # Diners Club
    '36227206271667',    # Diners Club 14-digit
    '3566002020360505',  # JCB
    '6200000000000005',  # UnionPay
    
    # Declined test cards (for testing error handling)
    '4000000000000101',  # CVC check fails
    '4000000000000341',  # Payment fails after tokenization
    '4000000000000002',  # Card declined
    '4000000000009995',  # Insufficient funds
    '4000000000009987',  # Lost card
    '4000000000009979',  # Stolen card
    '4000000000000069',  # Expired card
    '4000000000000127',  # Invalid CVC
    '4000000000000119',  # Gateway error
    '4242424242424241',  # Luhn check failure
}

# Successful ACH test accounts
JUSTIFI_TEST_ACH = {
    '110000000': ['000123456789'],  # Valid account
}

def validate_test_card(card_number: str, env_info: dict) -> None:
    """Validate card based on environment"""
    
    # Skip validation for non-production environments
    if env_info['is_staging'] or env_info['is_local']:
        logger.debug(f"Skipping test card validation for {env_info}")
        return
    
    # Production requires test cards
    if env_info['is_production']:
        clean_number = card_number.replace(' ', '').replace('-', '')
        if clean_number not in JUSTIFI_TEST_CARDS:
            raise ValidationError(
                f"Only JustiFi test cards are allowed in production. "
                f"Card {clean_number[:4]}... is not a recognized test card."
            )
```

#### Payment Creation Security
```python
# python/tools/payments_create.py

async def create_payment(
    client: JustiFiClient,
    amount: int,
    payment_method_id: str = None,
    card_number: str = None,
    card_exp_month: str = None,
    card_exp_year: str = None,
    card_cvc: str = None,
    description: str = None,
) -> dict:
    """Create a payment (test mode only for PCI compliance)
    
    Security layers:
    1. API key validation (test keys only in production)
    2. Test card validation (if raw card provided)
    3. Tokenization before payment
    """
    
    # Get environment info
    env_info = detect_environment(client.base_url, client.client_id)
    
    # Layer 1: Validate test mode for production
    if env_info['is_production'] and not env_info['is_test_key']:
        raise SecurityError(
            "Payment creation in production requires test API credentials. "
            "Use test_client_id and test_client_secret for prototyping."
        )
    
    # Layer 2: Validate test card if provided
    if card_number:
        validate_test_card(card_number, env_info)
        
        # Tokenize the card first (never store raw cards)
        payment_method_id = await tokenize_payment_method(
            client, card_number, card_exp_month, 
            card_exp_year, card_cvc
        )
    
    # Layer 3: Create payment with validated data
    return await client.request("POST", "/v1/payments", json={
        "amount": amount,
        "payment_method_id": payment_method_id,
        "description": description or f"Test payment - {datetime.now()}",
    })
```

### New Tools to Implement

#### File Structure
```
python/tools/
├── payments.py              # Existing (read-only, works in test & prod)
├── payments_create.py       # NEW: Payment creation (test-only)
├── payment_intents.py       # NEW: Payment intent operations
├── checkouts_create.py      # NEW: Checkout creation
├── utils/
│   ├── test_cards.py       # NEW: Test card validation
│   ├── environment.py      # NEW: Environment detection
│   └── security.py         # NEW: Security utilities
```

#### Tools List
1. **create_payment** - Direct payment with validation
2. **create_payment_intent** - Initialize payment flow
3. **capture_payment_intent** - Complete authorization
4. **tokenize_payment_method** - Card tokenization
5. **attach_payment_method** - Link method to intent
6. **create_checkout** - Generate checkout session
7. **update_checkout** - Modify checkout

---

## Phase 2: Web Component Integration

### Objective
Create comprehensive examples showing MCP + Web Components working together.

### Integration Patterns

#### Pattern 1: Embedded Checkout
```javascript
// 1. MCP creates checkout session
const checkout = await mcp.tools.create_checkout({
  amount: 2999,
  description: "Premium Plan",
  payment_method_group_id: null
});

// 2. Render Web Component
const element = document.createElement('justifi-checkout');
element.setAttribute('checkout-id', checkout.data.id);
element.setAttribute('client-id', 'test_...');
element.setAttribute('base-url', process.env.JUSTIFI_BASE_URL);

// 3. Handle completion
element.addEventListener('payment-complete', async (e) => {
  const payment = await mcp.tools.retrieve_payment({
    payment_id: e.detail.payment_id
  });
  console.log('Payment confirmed:', payment);
});
```

#### Pattern 2: Tokenization Flow
```javascript
// 1. Web Component captures card
const cardElement = document.createElement('justifi-card-form');
cardElement.setAttribute('tokenization-only', 'true');

// 2. MCP tokenizes and stores
cardElement.addEventListener('card-submitted', async (e) => {
  const token = await mcp.tools.tokenize_payment_method({
    card_number: e.detail.number,
    card_exp_month: e.detail.exp_month,
    card_exp_year: e.detail.exp_year,
    card_cvc: e.detail.cvc
  });
  
  // 3. Create payment with token
  const payment = await mcp.tools.create_payment({
    amount: 1999,
    payment_method_id: token.id
  });
});
```

### Example Projects

1. **examples/web-components/embedded-checkout/**
   - Full checkout flow with Web Components
   - MCP backend integration
   - Error handling

2. **examples/web-components/payment-form/**
   - Custom payment form
   - Tokenization flow
   - Saved payment methods

3. **examples/web-components/dashboard/**
   - Transaction list with MCP data
   - Real-time updates
   - Analytics visualization

4. **examples/web-components/marketplace/**
   - Split payments
   - Multi-party payouts
   - Platform fees

---

## Phase 3: Developer Experience Enhancement

### Quick Start Templates

#### E-commerce Template
```bash
npx @justifi/create-prototype ecommerce
# Generates:
# - Product catalog
# - Shopping cart
# - Checkout with Web Components
# - Order management with MCP
```

#### SaaS Subscription Template
```bash
npx @justifi/create-prototype subscription
# Generates:
# - Pricing page
# - Subscription signup
# - Recurring billing
# - Customer portal
```

### Intelligent Suggestions

```python
# python/tools/utils/suggestions.py

def suggest_next_tools(last_operation: str, context: dict) -> list:
    """AI-powered tool suggestions based on context"""
    
    suggestions = {
        'create_checkout': [
            'retrieve_checkout',
            'list_payments',
            'create_refund'
        ],
        'tokenize_payment_method': [
            'create_payment',
            'create_payment_intent',
            'create_payment_method_group'
        ],
        'create_payment_intent': [
            'capture_payment_intent',
            'retrieve_payment_intent',
            'cancel_payment_intent'
        ]
    }
    
    # Context-aware modifications
    if context.get('amount') > 10000:  # High value
        suggestions[last_operation].append('create_3ds_verification')
    
    return suggestions.get(last_operation, [])
```

---

## Phase 4: Advanced Prototyping Features

### Webhook Simulation
```python
# python/tools/testing/webhook_simulator.py

async def simulate_webhook(
    event_type: str,
    resource_id: str,
    custom_data: dict = None
) -> dict:
    """Simulate JustiFi webhook events for testing"""
    
    webhook_templates = {
        'payment.succeeded': {
            'id': f'evt_{uuid.uuid4()}',
            'type': 'payment.succeeded',
            'data': {
                'id': resource_id,
                'status': 'succeeded',
                'amount': custom_data.get('amount', 1000)
            }
        },
        'payment.failed': {
            'id': f'evt_{uuid.uuid4()}',
            'type': 'payment.failed',
            'data': {
                'id': resource_id,
                'status': 'failed',
                'failure_reason': custom_data.get('reason', 'card_declined')
            }
        }
    }
    
    return webhook_templates.get(event_type)
```

### Test Data Generation
```python
# python/tools/testing/data_generator.py

async def generate_test_scenario(
    scenario: str,
    count: int = 1
) -> list:
    """Generate realistic test data"""
    
    scenarios = {
        'successful_payments': generate_success_payments,
        'declined_payments': generate_declined_payments,
        'mixed_results': generate_mixed_payments,
        'refund_flow': generate_refund_scenario
    }
    
    generator = scenarios.get(scenario)
    return await generator(count)
```

---

## Implementation Timeline

### Week 1: Phase 0 + Phase 1 Start
- [ ] Implement base URL configuration enhancements
- [ ] Add environment detection utilities
- [ ] Create security validation framework
- [ ] Begin payment creation tools

### Week 2: Phase 1 Completion
- [ ] Complete all payment creation tools
- [ ] Implement test card validation
- [ ] Add comprehensive security tests
- [ ] Documentation for test-mode operations

### Week 3: Phase 2 Start
- [ ] Create Web Component integration examples
- [ ] Build embedded checkout demo
- [ ] Implement tokenization flow example

### Week 4: Phase 2 Completion
- [ ] Complete dashboard example
- [ ] Add marketplace demo
- [ ] Document integration patterns

### Week 5: Phase 3 Start
- [ ] Create quick-start templates
- [ ] Implement intelligent suggestions
- [ ] Build prototyping guides

### Week 6: Phase 3 Completion
- [ ] Complete all templates
- [ ] Add interactive tutorials
- [ ] Gather developer feedback

### Week 7: Phase 4 Start
- [ ] Implement webhook simulator
- [ ] Create test data generators
- [ ] Build debugging utilities

### Week 8: Phase 4 Completion
- [ ] Complete testing toolkit
- [ ] Add production migration guide
- [ ] Performance optimization

---

## Success Metrics

### Technical Metrics
- ✅ 100% test coverage for security validations
- ✅ < 100ms response time for all tools
- ✅ Zero PCI compliance violations
- ✅ All test cards properly validated

### Developer Experience Metrics
- 📊 < 2 hours to first working prototype
- 📊 < 30 minutes to embedded checkout
- 📊 > 90% successful first attempts
- 📊 > 4.5/5 developer satisfaction

### Business Metrics
- 📈 50% reduction in integration support tickets
- 📈 3x faster proof-of-concept development
- 📈 80% of prototypes convert to production
- 📈 30% increase in platform adoption

---

## Risk Mitigation

### Security Risks
| Risk | Mitigation |
|------|------------|
| Real card processing | Multi-layer validation, test-only enforcement |
| API key exposure | Environment variables, never in code |
| PCI violations | No raw card storage, tokenization only |

### Technical Risks
| Risk | Mitigation |
|------|------------|
| API changes | Version pinning, compatibility layer |
| Performance issues | Caching, async operations |
| Environment confusion | Clear detection and logging |

### Developer Experience Risks
| Risk | Mitigation |
|------|------------|
| Complexity | Progressive disclosure, clear examples |
| Setup difficulties | NPX wrapper, automated setup |
| Debugging challenges | Comprehensive logging, error messages |

---

## Security Checklist

### Before Phase 1 Release
- [ ] Test card validation working
- [ ] API key validation implemented
- [ ] No raw card storage possible
- [ ] Security tests passing
- [ ] Documentation includes warnings

### Before Production Use
- [ ] Security audit completed
- [ ] PCI compliance verified
- [ ] Rate limiting implemented
- [ ] Monitoring in place
- [ ] Incident response plan ready

---

## Notes and Considerations

### PCI Compliance
- Never store raw card numbers
- Always use tokenization
- Test cards only in MCP server
- Web Components handle sensitive data

### Environment Strategy
- Staging for integration testing
- Local for development
- Production with test keys for demos
- Never live keys for payment creation

### Documentation Priority
1. Security warnings first
2. Quick start guides
3. Complete API reference
4. Troubleshooting guide

---

## Appendix: Configuration Examples

### Staging Environment
```bash
export JUSTIFI_CLIENT_ID="test_staging_abc123"
export JUSTIFI_CLIENT_SECRET="test_staging_secret"
export JUSTIFI_BASE_URL="https://staging.api.justifi.ai"
```

### Local Development
```bash
export JUSTIFI_CLIENT_ID="test_local_xyz789"
export JUSTIFI_CLIENT_SECRET="test_local_secret"
export JUSTIFI_BASE_URL="http://localhost:3000"
```

### Production with Test Keys
```bash
export JUSTIFI_CLIENT_ID="test_prod_123"
export JUSTIFI_CLIENT_SECRET="test_prod_secret"
# JUSTIFI_BASE_URL defaults to https://api.justifi.ai
```

### Corporate Proxy
```bash
export JUSTIFI_CLIENT_ID="test_abc123"
export JUSTIFI_CLIENT_SECRET="test_secret"
export JUSTIFI_BASE_URL="https://api-proxy.company.com/justifi"
export HTTPS_PROXY="http://proxy.company.com:8080"
```

---

**END OF PLANNING DOCUMENT**

*Last Updated: [Will be updated as we refine the plan]*
*Status: DRAFT - DO NOT COMMIT*
