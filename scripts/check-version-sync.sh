#!/bin/bash

# Version Sync Validation Script
# Ensures all version sources are synchronized
# Used in CI to prevent version mismatches

set -e

echo "🔍 Checking version synchronization..."

# Get versions from different sources
GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "none")

# Get NPM version if we care about NPM (NPM_TOKEN is set)
if [ -n "$NPM_TOKEN" ] && command -v node &> /dev/null; then
    NPM_VERSION=$(node -p "require('./npx-wrapper/package.json').version" 2>/dev/null || echo "none")
elif [ -z "$NPM_TOKEN" ]; then
    NPM_VERSION="skipped"
else
    NPM_VERSION="unavailable"
fi

# Try to get Python version (may not work if setuptools-scm hasn't run)
PYTHON_VERSION="unknown"
if [ -f "python/_version.py" ]; then
    PYTHON_VERSION=$(python -c "import sys; sys.path.insert(0, 'python'); from _version import version; print(version)" 2>/dev/null || echo "unknown")
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
    
    if [ "$NPM_VERSION" != "unavailable" ] && [ "$NPM_VERSION" != "skipped" ] && [ "$NPM_VERSION" != "$GIT_VERSION_NO_V" ]; then
        echo "❌ ERROR: NPM version ($NPM_VERSION) doesn't match Git tag ($GIT_TAG)"
        echo "   Expected NPM version: $GIT_VERSION_NO_V"
        ERRORS=$((ERRORS + 1))
    elif [ "$NPM_VERSION" = "skipped" ]; then
        echo "ℹ️  NPM version check skipped (NPM_TOKEN not set)"
    elif [ "$NPM_VERSION" = "unavailable" ]; then
        echo "⚠️  WARNING: NPM version check skipped (node.js not available)"
    fi
    
    # Check Python version if available
    if [ "$PYTHON_VERSION" != "unknown" ]; then
        # Extract base version from Python version (handles dev versions like 1.0.11.dev0+g63fd504)
        PYTHON_BASE_VERSION=$(echo "$PYTHON_VERSION" | sed 's/\.dev.*$//')
        
        if [ "$PYTHON_BASE_VERSION" != "$GIT_VERSION_NO_V" ]; then
            echo "❌ ERROR: Python version ($PYTHON_VERSION) doesn't match Git tag ($GIT_TAG)"
            echo "   Expected Python base version: $GIT_VERSION_NO_V"
            echo "   Actual Python base version: $PYTHON_BASE_VERSION"
            ERRORS=$((ERRORS + 1))
        else
            if [[ "$PYTHON_VERSION" == *".dev"* ]]; then
                echo "ℹ️  Python version shows dev suffix (expected due to uncommitted changes)"
            fi
        fi
    fi
else
    # No git tag, check if we're in development
    if [ "$NPM_VERSION" = "none" ] && [ "$NPM_VERSION" != "unavailable" ] && [ "$NPM_VERSION" != "skipped" ]; then
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
    echo "1. Create a new release tag: git tag -a v1.0.1 -m 'Release v1.0.1' && git push origin v1.0.1"
    echo "2. GitHub Actions will automatically sync all versions"
    echo ""
    exit 1
fi 