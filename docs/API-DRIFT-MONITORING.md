# JustiFi API Drift Monitoring

## Overview

The JustiFi MCP server includes an automated API drift monitoring system that tracks changes in the JustiFi API specification. This ensures our MCP tools remain compatible with the latest JustiFi API and alerts us to any breaking changes.

## How It Works

### 🔄 Automated Monitoring
- **Schedule**: Runs every Monday at 9 AM UTC
- **Trigger**: Can also be manually triggered via GitHub Actions
- **Comparison**: Downloads latest JustiFi OpenAPI spec and compares with our stored version
- **Action**: Creates PRs and issues when changes are detected

### 📊 Change Detection
The system detects several types of changes:

#### Breaking Changes (High Priority)
- **Endpoint Removal**: Existing endpoints are removed
- **Schema Changes**: Required fields added/removed, data types changed
- **Authentication Changes**: Auth requirements modified
- **Parameter Changes**: Required parameters added/removed

#### Non-Breaking Changes (Low Priority)
- **New Endpoints**: Additional API endpoints added
- **Optional Fields**: New optional fields in responses
- **Documentation Updates**: Descriptions, examples updated
- **Version Updates**: API version increments

## Workflow Components

### 1. GitHub Actions Workflow
**File**: `.github/workflows/api-drift-monitor.yml`

```yaml
# Runs weekly and on manual trigger
# Downloads latest JustiFi OpenAPI spec
# Compares with stored version
# Creates PR and issue if changes detected
```

**Permissions Required**:
- `contents: write` - Update OpenAPI spec file
- `pull-requests: write` - Create PRs for changes
- `issues: write` - Create issues for notifications

### 2. CI Drift Check Script
**File**: `scripts/ci-drift-check.py`

**Functions**:
- Downloads latest JustiFi OpenAPI specification
- Loads our stored specification from `docs/justifi-openapi.yaml`
- Uses `deepdiff` to identify changes
- Categorizes changes as breaking vs non-breaking
- Generates change summaries
- Sets GitHub Actions outputs

### 3. Stored API Specification
**File**: `docs/justifi-openapi.yaml`

- **Source of Truth**: Our reference copy of the JustiFi API spec
- **Updated Automatically**: When changes are detected and PR is merged
- **Version Controlled**: All changes tracked in git history
- **Format**: YAML for human readability and git diffs

## Response to Changes

### When Changes Are Detected

1. **GitHub Issue Created**
   - **Title**: `API Drift Detected - YYYY-MM-DD`
   - **Labels**: `api-drift`, `needs-review`, `automated`
   - **Content**: Summary of changes, impact assessment, action items

2. **Pull Request Created**
   - **Title**: `chore: Update JustiFi API specification - YYYY-MM-DD`
   - **Content**: Updated OpenAPI spec file
   - **Review Required**: Manual review before merging

3. **Notifications**
   - Team is notified via GitHub notifications
   - Issue provides clear action items
   - PR includes review checklist

### Manual Review Process

#### For Breaking Changes
1. **Immediate Review**: High priority, review within 24 hours
2. **Impact Assessment**: Check which MCP tools are affected
3. **Tool Updates**: Update affected tools to maintain compatibility
4. **Testing**: Run full test suite and manual integration tests
5. **Documentation**: Update tool descriptions and endpoint inventory

#### For Non-Breaking Changes
1. **Standard Review**: Review within 1 week
2. **Opportunity Assessment**: Consider if new endpoints should be added as tools
3. **Documentation**: Update API specification reference
4. **Optional Updates**: Consider tool enhancements

## Affected MCP Tools

Our current **4 payout-focused tools** depend on these JustiFi API endpoints:

### Payout Tools
- **`retrieve_payout`** → `GET /payouts/{id}`
- **`list_payouts`** → `GET /payouts`
- **`get_payout_status`** → `GET /payouts/{id}` (status field)
- **`get_recent_payouts`** → `GET /payouts` (with limit)

### Monitoring Priority
- **High**: Changes to `/payouts` endpoints
- **Medium**: Changes to authentication/authorization
- **Low**: Changes to unrelated endpoints

## Configuration

### Environment Variables
- `GITHUB_TOKEN`: Required for creating PRs and issues
- `FORCE_UPDATE`: Optional, forces update even without changes

### Customization
- **Schedule**: Modify cron expression in workflow file
- **API URL**: Update JustiFi OpenAPI spec URL in script
- **Notification**: Modify issue/PR templates
- **Thresholds**: Adjust what constitutes "breaking" vs "non-breaking"

## Troubleshooting

### Common Issues

#### 1. API Spec Download Fails
```bash
❌ Failed to download OpenAPI spec: HTTPError
```
**Solution**: Check if JustiFi API spec URL is accessible and correct

#### 2. No Changes Detected Despite API Updates
**Possible Causes**:
- JustiFi hasn't updated their OpenAPI spec
- Our stored spec is already current
- Network issues preventing download

**Solution**: Use manual trigger with `force_update: true`

#### 3. False Positive Changes
**Cause**: Timestamp or metadata changes in spec
**Solution**: Update comparison logic to ignore non-functional changes

### Manual Testing

Test the drift detection locally:
```bash
cd scripts
python ci-drift-check.py
```

Test with force update:
```bash
FORCE_UPDATE=true python ci-drift-check.py
```

## Integration with Development Workflow

### Before Merging API Changes
1. **Review the PR**: Understand what changed in the API
2. **Run Tests**: Ensure `make test-local` passes (22/22 tests)
3. **Manual Testing**: Test affected tools with real API
4. **Update Tools**: Modify MCP tools if needed
5. **Update Documentation**: Reflect changes in README and docs

### After Merging
1. **Monitor**: Watch for any issues in production
2. **Validate**: Confirm tools work with updated API
3. **Document**: Update any affected documentation
4. **Communicate**: Notify team of significant changes

## Benefits

### 🛡️ Proactive Monitoring
- **Early Warning**: Detect API changes before they break tools
- **Automated**: No manual checking required
- **Comprehensive**: Covers all aspects of API specification

### 📋 Change Management
- **Documented**: All changes tracked in git history
- **Reviewed**: Manual review ensures quality
- **Tested**: Changes validated before deployment

### 🚀 Reliability
- **Up-to-date**: Always working with latest API version
- **Compatible**: Tools remain functional as API evolves
- **Predictable**: Structured response to API changes

## Future Enhancements

### Planned Improvements
1. **Semantic Versioning**: Track API version changes
2. **Impact Scoring**: Quantify the impact of changes
3. **Automated Testing**: Run integration tests on API changes
4. **Rollback Capability**: Quick revert if changes cause issues
5. **Multi-Environment**: Test changes in staging before production

### Advanced Features
- **Change Prediction**: ML-based prediction of likely changes
- **Dependency Mapping**: Visual map of tool → endpoint dependencies
- **Performance Monitoring**: Track API performance changes
- **Security Analysis**: Automated security impact assessment

---

**Note**: This monitoring system is essential for maintaining a production-ready MCP server that stays compatible with the evolving JustiFi API. 