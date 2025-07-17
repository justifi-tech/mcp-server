#!/bin/bash

# Version Sync Validation Script
# Ensures all version sources are synchronized
# Used in CI to prevent version mismatches

set -e

echo "🔍 Checking version synchronization..."

# Get versions from different sources
GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "none")
NPM_VERSION=$(node -p "require('./npx-wrapper/package.json').version" 2>/dev/null || echo "none")

# Try to get Python version (may not work if setuptools-scm hasn't run)
PYTHON_VERSION="unknown"
if [ -f "justifi_mcp/_version.py" ]; then
    PYTHON_VERSION=$(python -c "from justifi_mcp._version import version; print(version)" 2>/dev/null || echo "unknown")
elif command -v python &> /dev/null; then
    # Try to get version via setuptools-scm directly
    PYTHON_VERSION=$(python -c "import setuptools_scm; print(setuptools_scm.get_version())" 2>/dev/null || echo "unknown")
fi

echo ""
echo "📊 Version Report:"
echo "  Git Tag:     $GIT_TAG"
echo "  NPM:         $NPM_VERSION"  
echo "  Python:      $PYTHON_VERSION"
echo ""

# Validation logic
ERRORS=0

if [ "$GIT_TAG" != "none" ]; then
    # We have a git tag, check if NPM version matches
    GIT_VERSION_NO_V=${GIT_TAG#v}  # Remove 'v' prefix
    
    if [ "$NPM_VERSION" != "$GIT_VERSION_NO_V" ]; then
        echo "❌ ERROR: NPM version ($NPM_VERSION) doesn't match Git tag ($GIT_TAG)"
        echo "   Expected NPM version: $GIT_VERSION_NO_V"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check Python version if available
    if [ "$PYTHON_VERSION" != "unknown" ] && [ "$PYTHON_VERSION" != "$GIT_VERSION_NO_V" ]; then
        echo "❌ ERROR: Python version ($PYTHON_VERSION) doesn't match Git tag ($GIT_TAG)"
        echo "   Expected Python version: $GIT_VERSION_NO_V"
        ERRORS=$((ERRORS + 1))
    fi
else
    # No git tag, check if we're in development
    if [ "$NPM_VERSION" = "none" ]; then
        echo "❌ ERROR: Could not determine NPM version"
        ERRORS=$((ERRORS + 1))
    fi
    
    echo "ℹ️  No Git tag found - assuming development mode"
fi

# Final result
if [ $ERRORS -eq 0 ]; then
    echo "✅ All versions are synchronized!"
    exit 0
else
    echo ""
    echo "❌ Found $ERRORS version synchronization error(s)"
    echo ""
    echo "🔧 To fix version mismatches:"
    echo "1. Use the automated release script: ./scripts/release-automated.sh v1.0.1"
    echo "2. Or manually sync versions and create a proper Git tag"
    echo ""
    exit 1
fi 