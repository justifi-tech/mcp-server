# Dashboard Prototype

This example demonstrates building a real-world payment dashboard using the JustiFi API. The MCP server assists developers in their IDE by helping them understand data fetching patterns and generate backend code for analytics.

## Development Workflow

1. **IDE Integration**: Use MCP server in Cursor/Claude Code to explore data endpoints
2. **Backend Development**: Build analytics API that fetches real JustiFi data
3. **Dashboard Frontend**: Interactive dashboard calls your real backend
4. **Real-time Updates**: Live dashboard updates with actual payment data

## Features

- **Payment Overview**: Recent payments with status and amounts
- **Dispute Management**: Track and manage payment disputes
- **Balance Summary**: Current balance and recent transactions
- **Analytics Charts**: Visual representation of payment data
- **Search & Filter**: Find specific transactions quickly
- **Export Data**: Download transaction reports

## Prerequisites

- JustiFi test API credentials with existing transaction data
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

## MCP Tools Used

This dashboard demonstrates the following MCP tools:

- `list_payments` - Fetch recent payment transactions
- `list_disputes` - Get open and resolved disputes
- `list_refunds` - Show refund history
- `list_balance_transactions` - Display balance changes
- `retrieve_payment` - Get detailed payment information
- `retrieve_dispute` - Show dispute details

## Data Flow

```
1. Dashboard loads → MCP tools fetch data
   ↓
2. Data aggregated and processed
   ↓
3. Charts and tables updated
   ↓
4. Auto-refresh every 30 seconds
   ↓
5. User interactions trigger detail views
```

## Dashboard Sections

### 1. Summary Cards
- Total payments today
- Success rate
- Total refunded
- Open disputes

### 2. Recent Payments
- Last 10 transactions
- Payment status indicators
- Quick actions (refund, details)

### 3. Analytics Charts
- Payment volume over time
- Success/failure rates
- Payment methods breakdown

### 4. Disputes & Refunds
- Open disputes requiring attention
- Recent refunds processed
- Dispute resolution workflow

## Customization

The dashboard is designed to be easily customizable:

- **Styling**: Modify CSS variables for colors and fonts
- **Data Sources**: Add more MCP tools for additional data
- **Charts**: Replace Chart.js with your preferred library
- **Real-time**: Connect to webhooks for live updates

## Performance Considerations

- Data is cached for 30 seconds to reduce MCP calls
- Pagination used for large datasets
- Lazy loading for chart libraries
- Debounced search to prevent excessive filtering

## Security Features

- Read-only operations only
- No sensitive data displayed in clear text
- Test environment detection and warnings
- CORS and CSP headers recommended for production