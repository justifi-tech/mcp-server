# Single Source of Truth Versioning

## Overview

The JustiFi MCP Server uses a **single source of truth versioning system** where Git tags are the authoritative version source. This eliminates version mismatches and ensures all components stay synchronized.

## How It Works

### 🎯 Single Source of Truth: Git Tags

```
Git Tag (v1.0.1) → Python Version (1.0.1) → NPM Version (1.0.1)
```

1. **Git Tag**: The authoritative version (e.g., `v1.0.1`)
2. **Python Version**: Auto-derived from Git tag via `setuptools-scm`
3. **NPM Version**: Synced to match Git tag via release script

### 🔄 Automatic Version Derivation

- **setuptools-scm** reads Git tags and automatically sets Python package version
- **Release script** updates NPM package.json to match Git tag
- **CI validation** ensures all versions stay synchronized

## Version Sources

| Component | Location | Source | Example |
|-----------|----------|--------|---------|
| **Git Tag** | Repository | Manual/Script | `v1.0.1` |
| **Python Package** | `pyproject.toml` | setuptools-scm | `1.0.1` |
| **NPM Package** | `npx-wrapper/package.json` | Release script | `1.0.1` |
| **Python Module** | `justifi_mcp/__init__.py` | setuptools-scm | `1.0.1` |

## Creating Releases

### Method 1: Automated Release Script (Recommended)

```bash
# Create a new release - updates everything automatically
./scripts/release-automated.sh v1.0.1

# With NPM publishing (requires NPM_TOKEN)
NPM_TOKEN=your_token ./scripts/release-automated.sh v1.0.1
```

**What it does:**
1. ✅ Validates version format and prerequisites
2. ✅ Runs tests to ensure quality
3. ✅ Updates NPM package.json to match version (if NPM_TOKEN is set)
4. ✅ Commits version changes
5. ✅ Creates Git tag (triggers Python version via setuptools-scm)
6. ✅ Pushes changes and tag
7. ✅ Creates GitHub release

**NPM Publishing:**
- **With NPM_TOKEN**: Updates package.json and enables NPM publishing
- **Without NPM_TOKEN**: Skips NPM updates, Python-only release

### Method 2: Manual Process

```bash
# 1. Update NPM version
cd npx-wrapper
npm version 1.0.1 --no-git-tag-version
cd ..

# 2. Commit changes
git add npx-wrapper/package.json
git commit -m "chore: sync NPM version to 1.0.1 for release"

# 3. Create Git tag (triggers Python version)
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin main --tags

# 4. Create GitHub release
gh release create v1.0.1 --generate-notes
```

## Version Validation

### Check Version Sync

```bash
# Check if all versions are synchronized
make version-check
# or
./scripts/check-version-sync.sh

# With NPM token (checks NPM version)
NPM_TOKEN=your_token ./scripts/check-version-sync.sh
```

**Example output (with NPM_TOKEN):**
```
🔍 Checking version synchronization...

📊 Version Report:
  Git Tag:     v1.0.1
  NPM:         1.0.1
  Python:      1.0.1

✅ All versions are synchronized!
```

**Example output (without NPM_TOKEN):**
```
🔍 Checking version synchronization...

📊 Version Report:
  Git Tag:     v1.0.1
  NPM:         skipped
  Python:      1.0.1

ℹ️  NPM version check skipped (NPM_TOKEN not set)
✅ All versions are synchronized!
```

### CI Integration

The version validation runs in CI to prevent version mismatches:

```yaml
# .github/workflows/ci.yml
- name: Check version synchronization
  run: ./scripts/check-version-sync.sh
```

## Development Workflow

### Development Versions

During development (no Git tag):
- **Python**: `0.0.0` (setuptools-scm fallback)
- **NPM**: Whatever is in package.json
- **Git**: No tag

### Release Versions

After creating a release tag:
- **Python**: Auto-derived from Git tag (e.g., `1.0.1`)
- **NPM**: Synced to match Git tag (e.g., `1.0.1`)
- **Git**: Authoritative source (e.g., `v1.0.1`)

## Benefits

### ✅ Eliminates Version Mismatches
- Impossible to have different versions across components
- Git tag is the single source of truth
- Automatic synchronization prevents human error

### ✅ Simplified Release Process
- One command creates entire release
- No manual version updates needed
- Automatic CI validation

### ✅ Developer Experience
- Clear version hierarchy
- Automatic Python version derivation
- Consistent across all environments

## Troubleshooting

### Version Mismatch Detected

```bash
❌ ERROR: NPM version (1.0.0) doesn't match Git tag (v1.0.1)
   Expected NPM version: 1.0.1
```

**Solution:**
```bash
# Use the automated release script
./scripts/release-automated.sh v1.0.1
```

### Python Version Not Available

If `setuptools-scm` can't determine version:
- Ensure you're in a Git repository
- Check that Git tags exist
- Verify setuptools-scm is installed

### setuptools-scm Configuration

```toml
# pyproject.toml
[tool.setuptools_scm]
write_to = "justifi_mcp/_version.py"
fallback_version = "0.0.0"
```

## Migration from Old System

### Before (Multiple Sources)
```
pyproject.toml: version = "2.0.0-dev"
package.json: "version": "1.0.0"
__init__.py: __version__ = "2.0.0-dev"
Git tag: v1.0.0
```

### After (Single Source)
```
Git tag: v1.0.1 (authoritative)
├── Python: 1.0.1 (auto-derived)
├── NPM: 1.0.1 (synced)
└── Module: 1.0.1 (auto-derived)
```

## Best Practices

1. **Always use the automated release script** for releases
2. **Run version-check** before creating releases
3. **Follow semantic versioning** (v1.0.1, v1.1.0, v2.0.0)
4. **Test installations** after releases
5. **Use CI validation** to prevent version drift

## Commands Reference

```bash
# Create release
./scripts/release-automated.sh v1.0.1

# Check version sync
make version-check

# Validate in CI
./scripts/check-version-sync.sh

# Get current Python version
python -c "import justifi_mcp; print(justifi_mcp.__version__)"

# Get current NPM version
node -p "require('./npx-wrapper/package.json').version"
```

This system ensures that version mismatches are impossible and releases are fully automated and reliable. 