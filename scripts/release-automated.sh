#!/bin/bash

# Automated Release Script for JustiFi MCP Server
# Single Source of Truth Versioning with Git Tags
# Usage: ./scripts/release-automated.sh v1.0.1

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.1"
    echo ""
    echo "This script implements single source of truth versioning:"
    echo "1. Git tag becomes the authoritative version"
    echo "2. Python version auto-derived via setuptools-scm"
    echo "3. NPM package.json updated to match"
    echo "4. All versions stay in sync automatically"
    exit 1
fi

VERSION=$1
VERSION_NO_V=${VERSION#v}  # Remove 'v' prefix

# Validate version format (should start with v)
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format vX.Y.Z (e.g., v1.0.1)"
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch to create a release"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^$VERSION$"; then
    echo "❌ Error: Tag $VERSION already exists"
    exit 1
fi

echo "🚀 Starting automated release $VERSION..."
echo ""

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Run tests to ensure everything works
echo "🧪 Running tests..."
if command -v make &> /dev/null; then
    make test
else
    echo "⚠️  Make not available, skipping tests"
fi

# Update NPM package.json to match the new version
echo "📦 Updating NPM package.json to $VERSION_NO_V..."
cd npx-wrapper
npm version $VERSION_NO_V --no-git-tag-version
cd ..

# Commit version changes
echo "📝 Committing version sync..."
git add npx-wrapper/package.json
git commit -m "chore: sync NPM version to $VERSION_NO_V for release

- Updated package.json version to match Git tag
- Python version will be auto-derived from Git tag via setuptools-scm
- Maintains single source of truth versioning"

# Create and push the Git tag (this triggers Python version via setuptools-scm)
echo "🏷️  Creating Git tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION

🎯 Single Source of Truth Versioning:
- Git tag: $VERSION (authoritative)
- Python version: $VERSION_NO_V (auto-derived via setuptools-scm)
- NPM version: $VERSION_NO_V (synced in package.json)

✅ All versions automatically synchronized"

# Push changes and tag
echo "📤 Pushing changes and tag..."
git push origin main
git push origin "$VERSION"

# Create GitHub release
echo "🎉 Creating GitHub release..."
if command -v gh &> /dev/null; then
    gh release create "$VERSION" --title "JustiFi MCP Server $VERSION" --generate-notes
    echo "✅ GitHub release created: https://github.com/justifi-tech/mcp-server/releases/tag/$VERSION"
else
    echo "⚠️  GitHub CLI not available, please create release manually"
fi

echo ""
echo "🎉 Release $VERSION completed successfully!"
echo ""
echo "📋 Version Summary:"
echo "  Git Tag: $VERSION (single source of truth)"
echo "  Python: $VERSION_NO_V (auto-derived via setuptools-scm)"
echo "  NPM: $VERSION_NO_V (synced in package.json)"
echo ""
echo "🔗 Next steps:"
echo "1. Verify release: https://github.com/justifi-tech/mcp-server/releases/tag/$VERSION"
echo "2. Test Python install: pip install git+https://github.com/justifi-tech/mcp-server.git@$VERSION"
echo "3. Test NPM install: npx @justifi/mcp-server@$VERSION_NO_V"
echo ""
echo "✨ All versions are now automatically synchronized!" 