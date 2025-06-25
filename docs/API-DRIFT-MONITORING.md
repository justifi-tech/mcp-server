# JustiFi API Drift Monitoring

This document explains the automated API drift monitoring system for the JustiFi MCP server.

## Overview

The API drift monitoring system automatically detects changes in the JustiFi OpenAPI specification that could affect our 10 MCP tools. It runs weekly via GitHub Actions and can be executed locally for testing.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub        │    │   JustiFi API    │    │   Local Dev     │
│   Actions       │    │   OpenAPI Spec   │    │   Environment   │
│                 │    │                  │    │                 │
│ Weekly Cron ────┼────► Download Latest ◄────┼─── Manual Check │
│ Manual Trigger  │    │ Specification    │    │                 │
│ File Changes    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Drift Analysis Engine                        │
│                                                                 │
│  CI Script (scripts/ci-drift-check.py):                        │
│  • Download and compare OpenAPI specs                          │
│  • Monitor 10 endpoints used by our MCP tools                  │
│  • Detect additions, removals, and modifications               │
│  • Set GitHub Actions outputs for workflow decisions           │
│                                                                 │
│  Local Script (scripts/check-api-drift.py):                    │
│  • Same analysis logic for development use                     │
│  • Interactive output and optional spec updates                │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Response Actions                          │
│                                                                 │
│  No Changes:                   Critical Changes:                │
│  • Update stored spec          • Create GitHub issue           │
│  • Auto-commit changes        • Alert development team         │
│  • Continue monitoring        • Block spec updates             │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architecture Benefits
- **Clean separation**: CI logic in dedicated scripts, not inline YAML
- **Maintainable**: Python code is easier to test and debug than YAML
- **Reusable**: Same analysis logic for both CI and local development
- **Testable**: Scripts can be run and tested independently

## Monitored Endpoints

Our drift monitoring tracks these 10 endpoints that correspond to our MCP tools:

### Payment Tools (5)
- `POST /payments` → `create_payment`
- `GET /payments/{id}` → `retrieve_payment`
- `GET /payments` → `list_payments`
- `POST /payments/{id}/refunds` → `refund_payment`
- `GET /payments/{id}/refunds` → `list_refunds`

### Payment Method Tools (2)
- `POST /payment_methods` → `create_payment_method`
- `GET /payment_methods/{token}` → `retrieve_payment_method`

### Payout Tools (2)
- `GET /payouts/{id}` → `retrieve_payout`
- `GET /payouts` → `list_payouts`

### Balance Transaction Tools (1)
- `GET /balance_transactions` → `list_balance_transactions`

## Files

### GitHub Actions Workflow
- **File**: `.github/workflows/api-drift-monitor.yml`
- **Purpose**: Automated weekly monitoring with GitHub issue creation
- **Architecture**: Clean workflow that calls dedicated CI script
- **Triggers**:
  - Weekly schedule (Mondays at 9 AM UTC)
  - Manual workflow dispatch
  - Changes to endpoint inventory or stored spec

### CI Script
- **File**: `scripts/ci-drift-check.py`
- **Purpose**: CI/CD-optimized drift detection with GitHub Actions integration
- **Features**: GitHub Actions outputs, error codes, automated spec saving

### Local Development Script
- **File**: `scripts/check-api-drift.py`
- **Purpose**: Local development and testing of drift detection
- **Usage**:
  ```bash
  # Check for changes (read-only)
  make drift-check
  
  # Check and update spec if no breaking changes
  make drift-update
  
  # Direct script usage
  python scripts/check-api-drift.py --help
  ```

### Stored Specification
- **File**: `docs/justifi-openapi.yaml`
- **Purpose**: Baseline OpenAPI spec for comparison
- **Updates**: Automatically updated when no breaking changes detected

## How It Works

### 1. Specification Download
```python
# Downloads latest spec from JustiFi
JUSTIFI_OPENAPI_URL = "https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml"
```

### 2. Endpoint Extraction
```python
def extract_endpoint_info(spec: dict, endpoint_key: str) -> dict:
    """Extract endpoint information from OpenAPI spec"""
    # Handles parameter variations: {id} vs {payment_id}
    # Supports multiple path formats
    # Returns endpoint definition or None
```

### 3. Change Detection
The system detects three types of changes:

#### 🆕 New Endpoints
- Endpoint exists in latest spec but not in stored spec
- Could indicate new functionality available

#### 🚨 Removed Endpoints  
- Endpoint exists in stored spec but not in latest spec
- **CRITICAL**: Could break existing MCP tools

#### 🔄 Modified Endpoints
- Endpoint exists in both specs but with differences
- Uses `DeepDiff` for detailed comparison
- Could indicate parameter, response, or behavior changes

### 4. Response Actions

#### No Critical Changes
- ✅ Update stored OpenAPI spec automatically
- ✅ Commit changes to repository
- ✅ Continue monitoring

#### Critical Changes Detected
- 🚨 Create GitHub issue with detailed analysis
- 🚨 Block automatic spec updates
- 🚨 Alert development team
- 🚨 Exit with error code

## GitHub Actions Workflow Details

### Schedule
```yaml
schedule:
  # Run every Monday at 9 AM UTC (weekly check)
  - cron: '0 9 * * 1'
```

### Workflow Steps
1. **Checkout repository** with fetch-depth=2 for comparisons
2. **Set up Python 3.11** environment
3. **Install dependencies** (requests, pyyaml, deepdiff)
4. **Run API drift analysis** using `scripts/ci-drift-check.py`
5. **Update stored spec** if no critical changes (auto-commit)
6. **Create GitHub issue** if critical changes detected
7. **Post success comment** if all checks pass

The workflow is now much cleaner with the complex analysis logic extracted to a dedicated CI script.

### Issue Creation
When critical changes are detected, the workflow creates a GitHub issue with:

- **Title**: "🚨 JustiFi API Changes Detected - Review Required"
- **Labels**: `api-drift`, `breaking-change`, `high-priority`
- **Content**:
  - Summary of detected changes
  - List of affected MCP tools
  - Recommended actions checklist
  - Files that need review
  - Testing checklist

## Local Development

### Prerequisites
```bash
# Ensure dependencies are installed
make build-dev

# Verify environment
make env-check
```

### Commands

#### Basic Drift Check
```bash
make drift-check
```
- Downloads latest OpenAPI spec
- Compares with stored version
- Reports changes without modifying files
- Exit code 0 = no changes, 1 = changes detected

#### Drift Check with Update
```bash
make drift-update
```
- Same as drift-check
- Updates stored spec if no critical changes
- Commits changes to repository

#### Direct Script Usage
```bash
# Basic check
python scripts/check-api-drift.py

# Check with spec update
python scripts/check-api-drift.py --update-spec

# Verbose output
python scripts/check-api-drift.py --verbose

# Help
python scripts/check-api-drift.py --help
```

## Integration with Development Workflow

### Pre-Release Checks
```bash
# Include in release checklist
make drift-check
make test
make check-all
```

### Continuous Integration
The drift monitor integrates with our CI/CD pipeline:
1. **Weekly automated checks** catch API changes early
2. **Manual trigger capability** for immediate verification
3. **File change triggers** when endpoint inventory is updated
4. **GitHub issue creation** ensures team awareness

### Development Best Practices
1. **Run drift check** before major releases
2. **Review GitHub issues** created by drift monitor
3. **Update MCP tools** when API changes are detected
4. **Test thoroughly** after API changes
5. **Update documentation** to reflect changes

## Troubleshooting

### Common Issues

#### Script Fails to Download Spec
```bash
# Check network connectivity
curl -I https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml

# Verify URL is still valid
# Update JUSTIFI_OPENAPI_URL if needed
```

#### False Positives
- Some endpoints may have minor formatting differences
- Parameter naming variations ({id} vs {payment_id})
- The script handles common variations automatically

#### Missing Dependencies
```bash
# Rebuild container with latest requirements
make build-dev

# Verify dependencies
docker-compose run --rm dev pip list | grep -E "(requests|pyyaml|deepdiff)"
```

### Manual Verification
If you suspect the drift detection is incorrect:

1. **Download specs manually**:
   ```bash
   curl -o latest.yaml https://docs.justifi.tech/redocusaurus/plugin-redoc-0.yaml
   diff docs/justifi-openapi.yaml latest.yaml
   ```

2. **Test specific endpoints**:
   ```bash
   # Test with real API credentials
   make dev
   # Use MCP tools to verify functionality
   ```

3. **Review GitHub issues** for similar reports

## Security Considerations

### API Key Protection
- Drift monitoring does **NOT** require API keys
- Only downloads public OpenAPI specification
- No authentication needed for spec comparison

### Automated Commits
- Uses GitHub Actions bot account for commits
- Limited to updating OpenAPI spec file only
- No access to sensitive configuration

### Issue Creation
- Issues contain **NO sensitive information**
- Only includes endpoint paths and change types
- Safe for public repositories

## Maintenance

### Updating Monitored Endpoints
When adding new MCP tools:

1. **Update endpoint list** in both files:
   - `.github/workflows/api-drift-monitor.yml`
   - `scripts/check-api-drift.py`

2. **Update this documentation**

3. **Test the changes**:
   ```bash
   make drift-check
   ```

### Changing Schedule
Edit the cron expression in `.github/workflows/api-drift-monitor.yml`:
```yaml
schedule:
  - cron: '0 9 * * 1'  # Weekly on Monday at 9 AM UTC
```

### URL Updates
If JustiFi changes their OpenAPI spec URL:
1. Update `JUSTIFI_OPENAPI_URL` in `scripts/check-api-drift.py`
2. Update the curl command in `.github/workflows/api-drift-monitor.yml`
3. Test with `make drift-check`

## Success Metrics

The drift monitoring system is considered successful when:

- ✅ **Zero false negatives**: All breaking changes are detected
- ✅ **Minimal false positives**: Only real changes trigger alerts
- ✅ **Fast detection**: Changes detected within 1 week
- ✅ **Clear reporting**: Issues contain actionable information
- ✅ **Automated updates**: Non-breaking changes handled automatically
- ✅ **Developer friendly**: Easy local testing and debugging

## Future Enhancements

### Planned Improvements
1. **Semantic versioning detection** for API changes
2. **Automated tool update suggestions** based on detected changes
3. **Integration with release notes** from JustiFi
4. **Slack/Discord notifications** for critical changes
5. **Historical change tracking** and analytics

### Advanced Features
1. **Breaking change severity scoring** (low/medium/high impact)
2. **Automated regression testing** when changes detected
3. **Multi-environment monitoring** (sandbox vs production APIs)
4. **Custom webhook support** for external integrations 